Quick Employee Wizard
=====================

This module adds a GNU Health / Tryton wizard for fast employee admission.

Features
--------

* Creates or reuses the related ``party.party`` record.
* Creates the ``company.employee`` record including the custom ``cargo``
  field provided by ``z_health_employee``.
* Creates or completes the main ``party.address`` record.
* Creates or completes email and phone contact mechanisms.
* Opens the existing employee when the DNI / mocIDUP already belongs to one.

Business rules
--------------

* DNI / mocIDUP is stored in ``party.ref``.
* Existing data is never overwritten automatically.
* If the party exists without employee, the wizard reuses it and completes
  only empty fields.
* If more than one party uses the same DNI / mocIDUP, the wizard stops with
  an error.

Compatibility
-------------

* Python 3.10
* Tryton 6.0
* GNU Health 4.2
