"""Registre des décisions d’une demande : chaque étape qui pose une question le consulte (CLA-206).

Une décision est consommée par l’étape qui pose la question de même code ; une option hors de
celles de la question, ou une décision jamais consommée, est une erreur de saisie.
"""

from knitproof.domain.decision import Decision
from knitproof.domain.question import PendingQuestion


class DecisionError(Exception):
    """Une décision qui ne répond à aucune question posée, ou qui choisit hors des options."""


class Decisions:
    """Les décisions de la demande, par code de question, avec ce qui a été consommé."""

    def __init__(self, decisions: tuple[Decision, ...]) -> None:
        self._by_code: dict[str, Decision] = {}
        for decision in decisions:
            if decision.question in self._by_code:
                raise DecisionError(f"deux décisions pour la question « {decision.question} »")
            self._by_code[decision.question] = decision
        self._consumed: list[Decision] = []

    @property
    def consumed(self) -> tuple[Decision, ...]:
        return tuple(self._consumed)

    def answer(self, question: PendingQuestion) -> Decision | None:
        """La décision de même code, consommée ; `None` sans décision ; option inconnue refusée."""
        decision = self._by_code.get(question.code)
        if decision is None:
            return None
        if decision.choice not in question.options:
            raise DecisionError(
                f"décision sur « {question.code} » : « {decision.choice} » n’est pas un choix ; "
                f"choix possibles : {', '.join(question.options)}"
            )
        if decision not in self._consumed:
            self._consumed.append(decision)
        return decision

    def check_all_consumed(self) -> None:
        for code, decision in self._by_code.items():
            if decision not in self._consumed:
                reason = (
                    "aucune question de ce code n’est posée"
                    if code in ANSWERABLE_QUESTIONS
                    else "cette question ne se répond pas par une décision"
                )
                raise DecisionError(f"décision sur « {code} » : {reason} ; retirer la décision")
