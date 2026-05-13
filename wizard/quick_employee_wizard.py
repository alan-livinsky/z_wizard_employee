from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.wizard import Button, StateAction, StateView, Wizard


def _clean(value):
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


class QuickEmployeeStart(ModelView):
    'Inicio de Carga Rapida de Empleado'
    __name__ = 'z_wizard_employee.quick_employee.start'

    first_name = fields.Char('Nombre', required=True)
    last_name = fields.Char('Apellido', required=True)
    ref = fields.Char('DNI / IDUP', required=True)
    cuit = fields.Char('CUIT')
    gender = fields.Selection([
        (None, ''),
        ('m', 'Masculino'),
        ('f', 'Femenino'),
        ('nb', 'No binario'),
        ('other', 'Otro'),
        ('nd', 'No informado'),
        ('u', 'Desconocido'),
    ], 'Genero', required=True, sort=False)
    street = fields.Char('Calle', required=True)
    street_number = fields.Char('Numero')
    unit = fields.Char('Unidad')
    municipality = fields.Char('Municipio')
    city = fields.Char('Ciudad', required=True)
    zip = fields.Char('Codigo Postal')
    country = fields.Many2One('country.country', 'Pais', required=True)
    subdivision = fields.Many2One(
        'country.subdivision', 'Provincia',
        domain=[('country', '=', Eval('country'))],
        depends=['country'])
    email = fields.Char('Correo electronico')
    phone = fields.Char('Telefono')
    company = fields.Many2One(
        'company.company', 'Empresa contratante', required=True)
    start_date = fields.Date('Fecha de inicio', required=True)
    cargo = fields.Char('Cargo', required=True)
    supervisor = fields.Many2One(
        'company.employee', 'Supervisor',
        domain=[('company', '=', Eval('company'))],
        depends=['company'])

    @staticmethod
    def default_country():
        Country = Pool().get('country.country')
        countries = Country.search([
            ('code', '=', 'AR'),
        ], limit=1)
        if countries:
            return countries[0].id
        return None


class QuickEmployeeWizard(Wizard):
    'Carga Rapida de Empleado'
    __name__ = 'z_wizard_employee.quick_employee'

    start = StateView(
        'z_wizard_employee.quick_employee.start',
        'z_wizard_employee.quick_employee_start_view_form', [
            Button('Cancelar', 'end', 'tryton-cancel'),
            Button('Crear', 'create_employee', 'tryton-ok', default=True),
        ])
    create_employee = StateAction('company.act_employee_form')

    def do_create_employee(self, action):
        self._validate_start()

        employee = self._get_existing_employee()
        if employee:
            action['views'].reverse()
            action['name'] = gettext(
                'z_wizard_employee.msg_existing_employee_opening',
                employee=employee.rec_name,
                ref=_clean(self.start.ref))
            return action, {'res_id': [employee.id]}

        employee_id = self._create_or_update_records()
        action['views'].reverse()
        return action, {'res_id': [employee_id]}

    def transition_create_employee(self):
        return 'end'

    def _validate_start(self):
        if not _clean(self.start.first_name):
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_first_name'))
        if not _clean(self.start.last_name):
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_last_name'))
        if not _clean(self.start.ref):
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_ref'))
        if not self.start.gender:
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_gender'))
        if not _clean(self.start.street):
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_street'))
        if not _clean(self.start.city):
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_city'))
        if not self.start.country:
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_country'))
        if not self.start.company:
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_company'))
        if not self.start.start_date:
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_start_date'))
        if not _clean(self.start.cargo):
            raise UserError(gettext(
                'z_wizard_employee.msg_missing_cargo'))
        cuit = _clean(self.start.cuit)
        if cuit and not cuit.isdigit():
            raise UserError(gettext(
                'z_wizard_employee.msg_invalid_cuit'))

    def _get_party_by_ref(self, ref=None):
        Party = Pool().get('party.party')
        ref = _clean(ref if ref is not None else self.start.ref)
        parties = Party.search([('ref', '=', ref)])
        if len(parties) > 1:
            raise UserError(gettext(
                'z_wizard_employee.msg_duplicate_party_for_ref',
                ref=ref))
        return parties[0] if parties else None

    def _get_employee_for_party(self, party):
        Employee = Pool().get('company.employee')
        employees = Employee.search([('party', '=', party.id)], limit=1)
        return employees[0] if employees else None

    def _get_existing_employee(self):
        party = self._get_party_by_ref()
        if not party:
            return None
        return self._get_employee_for_party(party)

    def _create_or_update_records(self):
        pool = Pool()
        Party = pool.get('party.party')
        Employee = pool.get('company.employee')
        Address = pool.get('party.address')
        ContactMechanism = pool.get('party.contact_mechanism')
        AlternativePersonID = pool.get(
            'gnuhealth.person_alternative_identification')

        party = self._get_party_by_ref()
        if party:
            self._update_existing_party(party, Party)
        else:
            party, = Party.create([self._get_party_values()])

        self._create_missing_alternative_id(
            party, AlternativePersonID)
        self._create_or_update_address(party, Address)
        self._create_or_update_contacts(party, ContactMechanism)

        employee, = Employee.create([self._get_employee_values(party)])
        return employee.id

    def _get_party_values(self):
        Party = Pool().get('party.party')
        return {
            'name': _clean(self.start.first_name),
            'lastname': _clean(self.start.last_name),
            'ref': _clean(self.start.ref),
            'gender': self.start.gender,
            'fed_country': self._get_fed_country(Party),
            'citizenship': Party.default_citizenship(),
            'residence': Party.default_residence(),
            'is_person': True,
        }

    def _get_fed_country(self, Party):
        country = getattr(self.start, 'country', None)
        if country and getattr(country, 'code3', None):
            return country.code3
        return Party.default_fed_country() or 'XXX'

    def _update_existing_party(self, party, Party):
        values = {}
        if not party.name and _clean(self.start.first_name):
            values['name'] = _clean(self.start.first_name)
        if not getattr(party, 'lastname', None) and _clean(self.start.last_name):
            values['lastname'] = _clean(self.start.last_name)
        if not party.ref and _clean(self.start.ref):
            values['ref'] = _clean(self.start.ref)
        if not getattr(party, 'gender', None) and self.start.gender:
            values['gender'] = self.start.gender
        if not getattr(party, 'fed_country', None):
            values['fed_country'] = self._get_fed_country(Party)
        if not getattr(party, 'citizenship', None):
            values['citizenship'] = Party.default_citizenship()
        if not getattr(party, 'residence', None):
            values['residence'] = Party.default_residence()
        if not party.is_person:
            values['is_person'] = True
        if values:
            Party.write([party], values)

    def _create_missing_alternative_id(self, party, AlternativePersonID):
        cuit = _clean(self.start.cuit)
        if not cuit:
            return

        alternative_ids = AlternativePersonID.search([
            ('name', '=', party.id),
            ('alternative_id_type', '=', 'cuit'),
        ], limit=1)
        if alternative_ids:
            alternative_id = alternative_ids[0]
            if not alternative_id.code:
                AlternativePersonID.write([alternative_id], {
                    'code': cuit,
                })
            return

        AlternativePersonID.create([{
            'name': party.id,
            'code': cuit,
            'alternative_id_type': 'cuit',
        }])

    @staticmethod
    def _get_address_postal_field():
        Address = Pool().get('party.address')
        for field_name in ('zip', 'postal_code'):
            if field_name in Address._fields:
                return field_name
        return None

    def _create_or_update_address(self, party, Address):
        address = party.addresses[0] if party.addresses else None
        if address:
            values = {}
            street = self._compose_street()
            if not address.street and street:
                values['street'] = street
            if not address.city and _clean(self.start.city):
                values['city'] = _clean(self.start.city)
            postal_field = self._get_address_postal_field()
            if (postal_field and not getattr(address, postal_field, None)
                    and _clean(self.start.zip)):
                values[postal_field] = _clean(self.start.zip)
            if not address.country and self.start.country:
                values['country'] = self.start.country.id
            if not address.subdivision and self.start.subdivision:
                values['subdivision'] = self.start.subdivision.id
            if values:
                Address.write([address], values)
            return

        values = {
            'party': party.id,
            'street': self._compose_street(),
            'city': _clean(self.start.city),
            'country': self.start.country.id,
            'subdivision': (
                self.start.subdivision.id if self.start.subdivision else None),
        }
        postal_field = self._get_address_postal_field()
        if postal_field and _clean(self.start.zip):
            values[postal_field] = _clean(self.start.zip)
        Address.create([values])

    def _create_or_update_contacts(self, party, ContactMechanism):
        self._create_or_update_contact(
            party, ContactMechanism, 'email', _clean(self.start.email))
        self._create_or_update_contact(
            party, ContactMechanism, 'phone', _clean(self.start.phone))

    @staticmethod
    def _get_contact_mechanism(party, type_):
        for mechanism in party.contact_mechanisms:
            if mechanism.type == type_:
                return mechanism
        return None

    def _create_or_update_contact(self, party, ContactMechanism, type_, value):
        if not value:
            return
        mechanism = self._get_contact_mechanism(party, type_)
        if mechanism:
            if not mechanism.value:
                ContactMechanism.write([mechanism], {'value': value})
            return
        ContactMechanism.create([{
            'party': party.id,
            'type': type_,
            'value': value,
        }])

    def _get_employee_values(self, party):
        values = {
            'party': party.id,
            'company': self.start.company.id,
            'start_date': self.start.start_date,
            'cargo': _clean(self.start.cargo),
        }
        if self.start.supervisor:
            values['supervisor'] = self.start.supervisor.id
        return values

    def _compose_street(self):
        parts = [
            _clean(self.start.street),
            _clean(self.start.street_number),
            _clean(self.start.unit),
        ]
        return ' '.join([part for part in parts if part])
