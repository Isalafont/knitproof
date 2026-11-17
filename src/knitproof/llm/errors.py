"""Les erreurs de la couche llm (CLA-127)."""


class LlmError(Exception):
    """Racine des erreurs de la couche llm."""


class MissingSettingError(LlmError):
    """Une variable d’environnement obligatoire est absente ou vide."""

    def __init__(self, variable: str) -> None:
        super().__init__(f"{variable} : variable d’environnement manquante")
        self.variable = variable


class InvalidSettingError(LlmError):
    """Une variable d’environnement a une valeur refusée."""

    def __init__(self, variable: str, reason: str) -> None:
        super().__init__(f"{variable} : {reason}")
        self.variable = variable
        self.reason = reason


class ExtractionRejectedError(LlmError):
    """La sortie d’un modèle est refusée : hors schéma, ou sans nom de modèle rendu.

    `attempts` compte les essais HTTP, `latency_ms` la durée du seul essai qui a répondu.
    """

    def __init__(self, message: str, *, attempts: int = 1, latency_ms: int = 0) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.latency_ms = latency_ms


class TransientCallError(LlmError):
    """Les essais sont épuisés sur une erreur passagère (429, 5xx) ; la cause est `__cause__`."""

    def __init__(self, message: str, *, attempts: int) -> None:
        super().__init__(message)
        self.attempts = attempts
