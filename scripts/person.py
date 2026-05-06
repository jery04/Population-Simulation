"""Data model for a person in the population simulation."""

from typing import Optional  # Optional type hint for nullable partner references.
from dataclasses import dataclass  # Dataclass decorator for the person record.

# PERSON CLASS -------------------------------------------------
@dataclass
class Person:
    """Represents an individual in the population with demographic and social attributes."""
    id: int
    age: float  # años
    sex: str  # 'H' o 'M'
    has_partner: Optional["Person"] = None
    children_count: int = 0
    child_desire_count: int = 1
    desires_partner: bool = False
    time_left_single : float = 0.0  # months
    time_left_in_pregnancy: float = 0.0  # months
    is_alive: bool = True

    def age_up (self, time):
        """Age the person by one month."""
        # Increment age
        self.age += time
        
        # Decrement pregnancy timer if active
        if self.time_left_in_pregnancy > 0:
            self.time_left_in_pregnancy -= time
            if self.time_left_in_pregnancy < 0:
                self.time_left_in_pregnancy = 0
        
        # Decrement solitude timer if active
        if self.time_left_single  > 0:
            self.time_left_single  -= time
        elif self.time_left_single  < 0:
            self.time_left_single  = 0
            
    def is_single(self):
        """Check if person is alive, single, and ready for a new relationship."""
        # Verify all conditions: alive, no partner, solitude period expired
        return (
            self.is_alive and
            self.has_partner is None and
            self.time_left_single  <= 0
        )

    def is_able_to_reproduce(self):
        """Check if person can have children based on sex, status, and desires."""
        # Must be alive and female
        if not self.is_alive or self.sex != "M":
            return False
        # Must have a partner
        if self.has_partner is None:
            return False
        # Cannot be currently pregnant
        if self.time_left_in_pregnancy > 0:
            return False
        # Check if child count limit not reached
        limite = min(self.child_desire_count, self.has_partner.child_desire_count)
        return self.children_count < limite
