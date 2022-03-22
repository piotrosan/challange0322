import csv
from abc import ABC, abstractmethod

# Tutaj zastosowany został wzorzec Strategia
# przygotowane rozwiązanie pod ewentualne rozszerzenie o inne exportery


class Exporter(ABC):

    @abstractmethod
    def export(self, path):
        pass


class CSVExporter(Exporter):
    def __init__(self, headers, queryset):
        self.headers = headers
        self.queryset = queryset

    def prepare_data(self):
        result = list()
        for obj in self.queryset:
            row = dict()
            for header in self.headers:
                row[header] = getattr(obj, header)

            result.append(row)
        return result

    def export(self, path, delimiter=';'):
        with open(path, 'w') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                delimiter=delimiter,
                fieldnames=self.headers
            )
            writer.writeheader()
            writer.writerows(self.prepare_data())
