"""EcoleDirecte models."""

from __future__ import annotations

import re
from typing import Any


class EDEleve:
    """Student information."""

    def __init__(
        self,
        data: Any | None = None,
        establishment: Any | None = None,
        eleve_id: Any | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        classe_id: str | None = None,
        classe_name: str | None = None,
        modules: Any | None = None,
    ) -> None:
        """Initialize EDEleve."""
        if data is None:
            self.classe_id = classe_id
            self.classe_name: str = str({classe_name: ""})
            self.eleve_id = eleve_id
            self.eleve_lastname: str = str({last_name: ""})
            self.eleve_firstname: str = str({first_name: ""})
            self.modules = modules
            self.establishment = establishment
        else:
            if "classe" in data:
                self.classe_id = data["classe"]["id"]
                self.classe_name = data["classe"]["libelle"]
            self.eleve_id = data["id"]
            self.eleve_lastname = data["nom"]
            self.eleve_firstname = data["prenom"]
            self.establishment = establishment
            self.modules = []
            for module in data["modules"]:
                if module["enable"]:
                    self.modules.append(module["code"])

    def get_fullname_lower(self) -> str:
        """Student fullname lowercase."""
        return f"{re.sub('[^A-Za-z]', '_', self.eleve_firstname.lower())}_{
            re.sub('[^A-Za-z]', '_', self.eleve_lastname.lower())
        }"

    def get_fullname(self) -> str:
        """Student fullname."""
        return f"{self.eleve_firstname} {self.eleve_lastname}"
