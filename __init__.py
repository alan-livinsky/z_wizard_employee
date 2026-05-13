from trytond.pool import Pool

from . import health
from . import wizard


def register():
    Pool.register(
        health.AlternativePersonID,
        module='z_wizard_employee', type_='model')
    Pool.register(
        wizard.QuickEmployeeStart,
        module='z_wizard_employee', type_='model')
    Pool.register(
        wizard.QuickEmployeeWizard,
        module='z_wizard_employee', type_='wizard')
