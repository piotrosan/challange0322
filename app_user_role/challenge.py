import operator

from django.db import connection
from django.db.models import Q

from app_user_role.models import Client, Subscriber, SubscriberSMS, User
from exporter.exporter_api import CSVExporter


class IMigrate:
    register_migrates = list()

    @classmethod
    def auto_migrate(cls):
        if not cls.register_migrates:
            raise ValueError('Need register migrates')

        for migrate_class in cls.register_migrates:
            m = migrate_class()
            m.migrate()


class MetaMigrate(type):
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        IMigrate.register_migrates.append(instance)
        return instance


class BaseMigrate:

    # Tutaj miałem plan, żeby sterować jeszcze miejscem przechowywania pliku
    # ale niestety zabrakło mi czasu
    # w każdym razie zmienna EXPORT_DIRECOTRY zostawiona błędnie
    # ponieważ nie jest wykorzystywana jest zostawiona celowo

    EXPORT_DIRECTORY = ''

    def _get_double(self, clients):
        # tutaj też dwa rozwiązania
        # można napisać samemu albo skorzysytać z biblioteki która
        # sprawdza takie same elementy ale ja napiszę swoje rozwiązanie :)
        counter = dict()
        for client in clients:
            if client.phone in counter:
                counter[client.phone] += 1
            else:
                counter[client.phone] = 1
        return counter

    def _create_user_from_client(self, queryset):
        # tutaj widzę dwa rozwiązania albo po stronie bazy
        # jeśli możemy sobie pozwolić na jakieś zapytanie
        # double_phone = queryset.annotate(
        #    count=Count('phone')).values('phone', flat=True)
        elements = list(queryset)
        double = self._get_double(elements)
        bulk = list()
        double_phone_clinet = list()
        for client in elements:
            if client.phone in double and double[client.phone] > 1:
                double_phone_clinet.append(client)
                continue
            bulk.append(
                User(**{
                    'email': client.email,
                    'phone': client.phone,
                })
            )
        return User.objects.bulk_create(bulk), double_phone_clinet

    def _create_user_with_empty_phone(self, queryset):
        # tutaj widzę dwa rozwiązania albo po stronie bazy
        # jeśli możemy sobie pozwolić na jakieś zapytanie
        # double_phone = queryset.annotate(
        #    count=Count('phone')).values('phone', flat=True)
        elements = list(queryset)
        double = self._get_double(elements)
        bulk = list()
        double_phone_clinet = list()
        for client in elements:
            if client.phone in double and double[client.phone] > 1:
                double_phone_clinet.append(client)
                continue
            bulk.append(
                User(**{
                    'email': client.email,
                })
            )
        return User.objects.bulk_create(bulk), double_phone_clinet

    def create_user_from_client_model(self):
        client_for_create_user = Client.objects.filter(
            self._get_query_user_from_client()
        )
        migrated_client, double_phone_migrate = \
            self._create_user_from_client(client_for_create_user)

        if not double_phone_migrate:
            return
        exporter = CSVExporter(['id', 'email', 'phone'], double_phone_migrate)
        exporter.export('migrate_conflict_double_phone.csv')

    def export_subscriber(self):
        subscriber_for_export = self._get_subscriber_exists().filter(
            self._get_query_export_subscriber()
        )
        exporter = CSVExporter(['id', 'email'], subscriber_for_export)
        exporter.export('subscriber_conflicts.csv')

    def create_user_with_empty_phone_model(self):
        user_with_empty_phone = Client.objects.filter(
            self._get_query_user_with_empty_phone()
        )
        migrated_client_with_no_phone, double_with_empty = \
            self._create_user_with_empty_phone(user_with_empty_phone)

        if not double_with_empty:
            return
        exporter = CSVExporter(['id', 'email', 'phone'], double_with_empty)
        exporter.export('double_with_empty.csv')

    def migrate(self):
        self.create_user_from_client_model()
        self.export_subscriber()
        self.create_user_with_empty_phone_model()


class MigrateSubscriber(BaseMigrate, metaclass=MetaMigrate):
    def _get_subscriber_exists(self):
        return Subscriber.objects.filter(
            ~Q(email__in=User.objects.values('email'))
        )

    def _get_query_user_with_empty_phone(self):
        return ~Q(email__in=self._get_subscriber_exists().values('email'))

    def _get_query_export_subscriber(self):
        return Q(email__in=Client.objects.filter(
                phone__in=User.objects.values('phone')
            ).filter(
                ~Q(email__in=User.objects.values('email'))
            ).values('email'))

    def _get_query_user_from_client(self):
        query_filter = operator.and_(
            Q(email__in=self._get_subscriber_exists().values('email')),
            ~Q(phone__in=User.objects.values('phone')),
        )
        return operator.and_(
            query_filter,
            ~Q(email__in=User.objects.values('email'))
        )


class MigrateSubscriberSMS(BaseMigrate, metaclass=MetaMigrate):
    def _get_subscriber_exists(self):
        return SubscriberSMS.objects.filter(
            Q(phone__in=User.objects.values('phone'))
        )

    def _get_query_user_with_empty_phone(self):
        return Q(phone__in=self._get_subscriber_exists().values('phone'))

    def _get_query_export_subscriber(self):
        return Q(phone__in=Client.objects.filter(
                        ~Q(phone__in=User.objects.values('phone'))
                    ).filter(
                        Q(email__in=User.objects.values('email'))
                    ).values('phone')
                 )

    def _get_query_user_from_client(self):
        query_filter = operator.and_(
            ~Q(phone__in=self._get_subscriber_exists().values('phone')),
            Q(phone__in=User.objects.values('phone')),
        )
        return operator.and_(
            query_filter,
            Q(email__in=User.objects.values('email'))
        )


class MigrateUpdateSQL:

    @property
    def sql(self):
        return self.update_from_subscriber()

    def migrate(self):
        with connection.cursor() as cursor:
            cursor.execute(self.sql)


class MigrateSubscriberSQL(MigrateUpdateSQL, metaclass=MetaMigrate):

    # SQL miał być ładnie podzielony i wykorzystane WITH statement
    # ale SQLite nie pozwolil niestety na to więc został przygotowany
    # caly jeden SQL

    def update_from_subscriber(self):
        return """
            UPDATE app_user_role_user
            SET
                gdpr_consent = su.gdpr_consent_correct
            FROM app_user_role_user u
            JOIN ( 
                SELECT 
                    s.email, 
                    (CASE
                        WHEN u.email IN (
                            SELECT c.email FROM app_user_role_client c
                            JOIN app_user_role_subscribersms ss on ss.phone = c.phone
                            JOIN app_user_role_subscriber s on s.email = c.email
                            WHERE 
                                s.create_date < ss.create_date 
                        ) 
                        THEN ss.gdpr_consent
                        ELSE s.gdpr_consent
                    END) as gdpr_consent_correct
                FROM app_user_role_subscriber s
                JOIN app_user_role_user u on s.email = u.email
                LEFT JOIN app_user_role_subscribersms ss on u.phone = ss.phone 
                WHERE 
                    s.create_date < u.create_date 
             ) su on su.email = u.email
             WHERE 
                app_user_role_user.id = u.id
        """ # noqa 501
