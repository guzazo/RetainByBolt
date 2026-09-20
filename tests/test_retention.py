import unittest

from retention import (
    PRESET_B2C,
    PRESET_SAAS,
    Modulo,
    PerfilDeRisco,
    Sinal,
    at_risk,
    build_profiles,
    forecast_client_risk,
    normalize_weights,
    recommended_weight_evidence,
)


class DynamicRiskEngineTests(unittest.TestCase):
    def test_weights_are_normalized(self):
        normalized = normalize_weights({"A": 30, "B": 10})
        self.assertAlmostEqual(sum(normalized.values()), 100)
        self.assertEqual(normalized["A"], 75)

    def test_missing_signal_is_redistributed_and_reduces_coverage(self):
        module = Modulo("m", "Módulo", 100, (
            Sinal("available", "Disponível", 60, valor_normalizado=80),
            Sinal("missing", "Ausente", 40, valor_normalizado=None),
        ))
        result = module.calcular()
        self.assertIsNotNone(result)
        self.assertEqual(result.score, 80)
        self.assertAlmostEqual(result.cobertura, 0.60)
        self.assertEqual(result.pesos_redistribuidos["available"], 100)

    def test_missing_module_is_redistributed_but_lowers_confidence(self):
        available = Modulo("a", "A", 60, (Sinal("x", "X", 100, valor_normalizado=80),))
        missing = Modulo("b", "B", 40, (Sinal("y", "Y", 100, valor_normalizado=None),))
        result = PerfilDeRisco((available, missing)).calcular()
        self.assertEqual(result.score, 80)
        self.assertEqual(result.confianca, 60)
        self.assertEqual(result.pesos_redistribuidos["a"], 100)

    def test_disabled_module_does_not_lower_confidence(self):
        available = Modulo("a", "A", 60, (Sinal("x", "X", 100, valor_normalizado=80),))
        disabled = Modulo("b", "B", 40, (Sinal("y", "Y", 100, valor_normalizado=None),), ativo=False)
        result = PerfilDeRisco((available, disabled)).calcular()
        self.assertEqual(result.score, 80)
        self.assertEqual(result.confianca, 100)

    def test_all_modules_disabled_is_safe(self):
        module = Modulo("a", "A", 100, (Sinal("x", "X", 100, valor_normalizado=90),), ativo=False)
        result = PerfilDeRisco((module,)).calcular()
        self.assertEqual(result.score, 0)
        self.assertEqual(result.confianca, 0)
        self.assertEqual(result.sinais_ativos, 0)


class PresetIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saas = build_profiles(PRESET_SAAS)
        cls.b2c = build_profiles(PRESET_B2C)

    def test_only_active_clients_are_scored(self):
        self.assertEqual(len(self.saas), 58)
        self.assertEqual(len(self.b2c), 58)

    def test_presets_activate_different_modules(self):
        saas_ids = {module.id for module in self.saas[0].module_results}
        b2c_ids = {module.id for module in self.b2c[0].module_results}
        self.assertIn("operacao", saas_ids)
        self.assertIn("transacao", b2c_ids)
        self.assertNotIn("operacao", b2c_ids)
        self.assertNotIn("transacao", saas_ids)

    def test_risk_and_priority_are_separate(self):
        for profile in self.saas + self.b2c:
            self.assertAlmostEqual(
                profile.exposed_value,
                profile.economic_value * profile.risk_score / 100,
                delta=0.01,
            )

    def test_scores_and_confidence_are_bounded(self):
        for profile in self.saas + self.b2c:
            self.assertTrue(0 <= profile.risk_score <= 100)
            self.assertTrue(0 <= profile.confidence <= 100)

    def test_at_risk_excludes_low_risk(self):
        self.assertTrue(all(profile.risk_level != "Baixo" for profile in at_risk(self.saas)))

    def test_disabling_whole_modules_keeps_queue_operational(self):
        settings = {
            "operacao": {"active": False, "weight": 30},
            "suporte": {"active": False, "weight": 20},
            "cs": {"active": False, "weight": 20},
            "adocao": {"active": True, "weight": 15},
            "satisfacao": {"active": False, "weight": 10},
            "financeiro": {"active": False, "weight": 5},
        }
        profiles = build_profiles(PRESET_SAAS, settings)
        self.assertEqual(len(profiles), 58)
        self.assertTrue(all(set(p.module_weights) <= {"adocao"} for p in profiles))
        self.assertTrue(all(p.confidence == 100 for p in profiles))

    def test_recommended_weights_come_from_historical_comparison(self):
        evidence = recommended_weight_evidence(PRESET_SAAS)
        self.assertEqual(len(evidence), 6)
        self.assertAlmostEqual(sum(item.recommended_weight for item in evidence), 100, delta=0.2)
        self.assertTrue(all(item.source_signals for item in evidence))
        self.assertTrue(any(item.difference > 0 for item in evidence))

    def test_forecast_has_three_bounded_future_points(self):
        forecast = forecast_client_risk("C080", PRESET_SAAS)
        self.assertEqual(len(forecast.actual_scores), 6)
        self.assertTrue(all(0 <= value <= 100 for value in forecast.forecast_scores))

    def test_validate_default_dataset(self):
        from retention import DATA_PATH, validate_dataset
        is_valid, errors, summary = validate_dataset(DATA_PATH)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertEqual(summary["total_clients"], 80)
        self.assertEqual(summary["active_clients"], 58)
        self.assertEqual(summary["canceled_clients"], 22)

    def test_validate_invalid_dataset(self):
        import io
        from retention import validate_dataset
        invalid_bytes = io.BytesIO(b"not an excel file")
        is_valid, errors, summary = validate_dataset(invalid_bytes)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)


if __name__ == "__main__":
    unittest.main()
