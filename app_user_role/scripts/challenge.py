from ..models import Subscriber, SubscriberSMS, User, Client
from django.db.models import Q, Count
from exporter.exporter_api import CSVExporter
import operator
from django.db import connection


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
            if client.phone in double:
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
            self.create_user_with_empty_phone(user_with_empty_phone)

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

    def _get_query_export_subscriber(self, sms):
        return Q(email=Client.objects.filter(
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
        return Q(email__in=self._get_subscriber_exists().values('email'))

    def _get_query_export_subscriber(self):
        return Q(email=Client.objects.filter(
                ~Q(phone__in=User.objects.values('phone'))
            ).filter(
                Q(email__in=User.objects.values('email'))
            ).values('email'))

    def _get_query_user_from_client(self):
        query_filter = operator.and_(
            ~Q(email__in=self._get_subscriber_exists().values('phone')),
            Q(phone__in=User.objects.values('phone')),
        )
        return operator.and_(
            query_filter,
            Q(email__in=User.objects.values('email'))
        )


class MigrateSubscriberChallenge2(metaclass=MetaMigrate):

    # tutaj założyłem być może błędnie, że SubscriberSMS
    # powinien mieć podobne założenia jak Subscriber czyli
    # data powinna być wcześniejsza niż u usera

    def with_sql_subscriber(self):
        return """
            WITH tmp_sub as (
                SELECT * FROM app_user_role_subscriber
                JOIN app_user_role_user u on s.email = u.email
                WHERE
                    s.create_date > u.create_date 
            )
            WITH tmp_sub_sms as (
                SELECT * FROM app_user_role_subscribersms ss
                JOIN app_user_role_user u on ss.phone = u.phone
                WHERE
                    ss.create_date > u.create_date 
            )
            WITH subscriber as  ( 
                SELECT * FROM tmp_sub
                WHERE email IN ( 
                    SELECT * FROM app_user_role_client c
                    JOIN app_user_role_subscribersms ss on ss.phone = c.phone
                    JOIN app_user_role_subscriber s on s.email = c.email
                    WHERE 
                        s.create_date > ss.create_date
            )
            WITH subscriber_sms as ( 
                SELECT * FROM tmp_sub_sms
                WHERE email IN ( 
                    SELECT * FROM app_user_role_client c
                    JOIN app_user_role_subscribersms ss on ss.phone = c.phone
                    JOIN app_user_role_subscriber s on s.email = c.email
                    WHERE 
                        ss.create_date > s.create_date
            )        
        """

    def update_from_subscriber(self):
        return """
            UPDATE app_user_role_user
            SET
                gdpr_consent = s.gdpr_consent
            FROM subscriber s
            WHERE s.email = email
        """

    def update_from_subscriber_sms(self):
        return """
            UPDATE app_user_role_user
            SET
                gdpr_consent = ss.gdpr_consent
            FROM subscriber_sms ss
            WHERE ss.phone = phone
        """

    @property
    def sql(self):
        return f"""
            {self.with_sql_subscriber()}
            {self.update_from_subscriber()}
            {self.update_from_subscriber_sms()}
        """

    def migrate(self):
        with connection.cursor() as cursor:
            cursor.execute(self.sql)


