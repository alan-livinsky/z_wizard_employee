from trytond.pool import PoolMeta


class AlternativePersonID(metaclass=PoolMeta):
    __name__ = 'gnuhealth.person_alternative_identification'

    @classmethod
    def __setup__(cls):
        super(AlternativePersonID, cls).__setup__()
        if ('cuit', 'CUIT') not in cls.alternative_id_type.selection:
            cls.alternative_id_type.selection.append(('cuit', 'CUIT'))
