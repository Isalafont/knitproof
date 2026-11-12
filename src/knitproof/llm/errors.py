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
    """La sortie d’un modèle est refusée : hors schéma, ou sans nom de modèle rendu."""
