"""
Management command to populate initial age group mappings for Arena-SGE integration.
Usage: python manage.py populate_age_groups
"""

from django.core.management.base import BaseCommand
from apps.normalization.models import AgeGroupMapping

ARENA_BASE_AUDIENCES = {
    "audiences": {
        "seniors": {
            "identifier": "seniors",
            "name": "Seniors",
            "minAge": 18,
            "maxAge": 60
        },
        "u23": {
            "identifier": "u23",
            "name": "U23",
            "minAge": 18,
            "maxAge": 23
        },
        "u20": {
            "identifier": "u20",
            "name": "U20",
            "minAge": 17,
            "maxAge": 20
        },
        "u17": {
            "identifier": "u17",
            "name": "U17",
            "minAge": 16,
            "maxAge": 17
        },
        "u16": {
            "identifier": "u16",
            "name": "U16",
            "minAge": 14,
            "maxAge": 16
        },
        "equipes-base": {
            "identifier": "equipes-base",
            "name": "equipes base",
            "minAge": 13,
            "maxAge": 20
        },
        "equipes-senior": {
            "identifier": "equipes-senior",
            "name": "equipes senior",
            "minAge": 18,
            "maxAge": 35
        },
        "u15": {
            "identifier": "u15",
            "name": "U15",
            "minAge": 14,
            "maxAge": 15
        },
        "u13": {
            "identifier": "u13",
            "name": "U13",
            "minAge": 12,
            "maxAge": 13
        },
        "u11": {
            "identifier": "u11",
            "name": "U11",
            "minAge": 10,
            "maxAge": 11
        },
        "u9": {
            "identifier": "u9",
            "name": "U9",
            "minAge": 8,
            "maxAge": 9
        },
        "veterans-a": {
            "identifier": "veterans-a",
            "name": "Veterans A",
            "minAge": 35,
            "maxAge": 40
        },
        "veterans-b": {
            "identifier": "veterans-b",
            "name": "Veterans B",
            "minAge": 41,
            "maxAge": 45
        },
        "veterans-c": {
            "identifier": "veterans-c",
            "name": "Veterans C",
            "minAge": 46,
            "maxAge": 50
        },
        "veterans-d": {
            "identifier": "veterans-d",
            "name": "Veterans D",
            "minAge": 51,
            "maxAge": 55
        },
        "veterans-e": {
            "identifier": "veterans-e",
            "name": "Veterans E",
            "minAge": 56,
            "maxAge": 60
        },
        "veterans-f": {
            "identifier": "veterans-f",
            "name": "Veterans F",
            "minAge": 61,
            "maxAge": 65
        },
        "veterans-g": {
            "identifier": "veterans-g",
            "name": "Veterans G",
            "minAge": 66,
            "maxAge": 70
        },
        "veterans-all": {
            "identifier": "veterans-all",
            "name": "Veterans All",
            "minAge": 35,
            "maxAge": 56
        },
        "inf-11-12": {
            "identifier": "inf-11-12",
            "name": "inf-11-12",
            "minAge": 11,
            "maxAge": 12
        },
        "inf-7-8": {
            "identifier": "inf-7-8",
            "name": "inf-7-8",
            "minAge": 7,
            "maxAge": 8
        },
        "inf-9-10": {
            "identifier": "inf-9-10",
            "name": "inf-9-10",
            "minAge": 9,
            "maxAge": 10
        }
    }
}
SGE_ID_CLASSE_PESO_BASE = [
  {
    "categoria": "Veteranos A"
  },
  {
    "categoria": "Sênior"
  },
  {
    "categoria": "Infantil 7 e 8"
  },
  {
    "categoria": "U-23"
  },
  {
    "categoria": "Sub-17"
  },
  {
    "categoria": "Sub-15"
  },
  {
    "categoria": "Infantil 9 e 10"
  },
  {
    "categoria": "Sub-20"
  },
  {
    "categoria": "Sub-16"
  },
  {
    "categoria": "Infantil 11 e 12"
  }
]

SGE_RANK_ARENA_ENDPOINT_BASE = [
  {
    "audienceName": "inf-11-12"
  },
  {
    "audienceName": "U15"
  },
  {
    "audienceName": "U16"
  },
  {
    "audienceName": "veterans-a"
  },
  {
    "audienceName": "inf-7-8"
  },
  {
    "audienceName": "U23"
  },
  {
    "audienceName": "U17"
  },
  {
    "audienceName": "U20"
  },
  {
    "audienceName": "Seniors"
  },
  {
    "audienceName": "inf-9-10"
  },
  {
    "audienceName": "seniors"
  },
  {
    "audienceName": "Veterans A"
  }
]


class Command(BaseCommand):
    help = 'Populate initial age group mappings for Arena-SGE integration based on real-world data'

    def handle(self, *args, **options):
        # Mappings based on actual Arena and SGE data
        # canonical_name uses Arena identifier
        # arena_variations include all observed Arena naming patterns
        # sge_variations include all SGE category variations (first is primary)
        mappings = [
            {
                'canonical_name': 'seniors',
                'arena_variations': ['seniors', 'Seniors', 'Senior', 'SENIOR', 'Sênior', 'SÊNIOR', 'Adulto', 'ADULTO'],
                'sge_variations': ['Sênior', 'Senior', 'SENIOR'],
                'sort_order': 100,
            },
            {
                'canonical_name': 'u23',
                'arena_variations': ['u23', 'U23', 'U-23', 'Sub-23', 'SUB 23', 'Under 23'],
                'sge_variations': ['U-23', 'U23', 'Sub-23', 'SUB 23'],
                'sort_order': 90,
            },
            {
                'canonical_name': 'u20',
                'arena_variations': ['u20', 'U20', 'U-20', 'Sub-20', 'SUB 20', 'Under 20', 'Juvenil'],
                'sge_variations': ['Sub-20', 'SUB 20', 'U20', 'U-20'],
                'sort_order': 80,
            },
            {
                'canonical_name': 'u17',
                'arena_variations': ['u17', 'U17', 'U-17', 'Sub-17', 'SUB 17', 'Under 17', 'Cadete'],
                'sge_variations': ['Sub-17', 'SUB 17', 'U17', 'U-17'],
                'sort_order': 70,
            },
            {
                'canonical_name': 'u16',
                'arena_variations': ['u16', 'U16', 'U-16', 'Sub-16', 'SUB 16', 'Under 16'],
                'sge_variations': ['Sub-16', 'SUB 16', 'U16', 'U-16'],
                'sort_order': 65,
            },
            {
                'canonical_name': 'u15',
                'arena_variations': ['u15', 'U15', 'U-15', 'Sub-15', 'SUB 15', 'Under 15', 'Infantil'],
                'sge_variations': ['Sub-15', 'SUB 15', 'U15', 'U-15'],
                'sort_order': 60,
            },
            {
                'canonical_name': 'u13',
                'arena_variations': ['u13', 'U13', 'U-13', 'Sub-13', 'SUB 13', 'Under 13', 'Pré-Infantil'],
                'sge_variations': ['Sub-13', 'SUB 13', 'U13', 'U-13'],
                'sort_order': 50,
            },
            {
                'canonical_name': 'u11',
                'arena_variations': ['u11', 'U11', 'U-11', 'Sub-11', 'SUB 11', 'Under 11'],
                'sge_variations': ['Sub-11', 'SUB 11', 'U11', 'U-11'],
                'sort_order': 40,
            },
            {
                'canonical_name': 'u9',
                'arena_variations': ['u9', 'U9', 'U-9', 'Sub-9', 'SUB 9', 'Under 9'],
                'sge_variations': ['Sub-9', 'SUB 9', 'U9', 'U-9'],
                'sort_order': 30,
            },
            {
                'canonical_name': 'veterans-a',
                'arena_variations': ['veterans-a', 'Veterans A', 'Veteranos A', 'VETERANS A', 'Veterano A'],
                'sge_variations': ['Veteranos A', 'Veterans A', 'VETERANOS A'],
                'sort_order': 110,
            },
            {
                'canonical_name': 'veterans-b',
                'arena_variations': ['veterans-b', 'Veterans B', 'Veteranos B', 'VETERANS B', 'Veterano B'],
                'sge_variations': ['Veteranos B', 'Veterans B', 'VETERANOS B'],
                'sort_order': 111,
            },
            {
                'canonical_name': 'veterans-c',
                'arena_variations': ['veterans-c', 'Veterans C', 'Veteranos C', 'VETERANS C', 'Veterano C'],
                'sge_variations': ['Veteranos C', 'Veterans C', 'VETERANOS C'],
                'sort_order': 112,
            },
            {
                'canonical_name': 'veterans-d',
                'arena_variations': ['veterans-d', 'Veterans D', 'Veteranos D', 'VETERANS D', 'Veterano D'],
                'sge_variations': ['Veteranos D', 'Veterans D', 'VETERANOS D'],
                'sort_order': 113,
            },
            {
                'canonical_name': 'veterans-e',
                'arena_variations': ['veterans-e', 'Veterans E', 'Veteranos E', 'VETERANS E', 'Veterano E'],
                'sge_variations': ['Veteranos E', 'Veterans E', 'VETERANOS E'],
                'sort_order': 114,
            },
            {
                'canonical_name': 'veterans-f',
                'arena_variations': ['veterans-f', 'Veterans F', 'Veteranos F', 'VETERANS F', 'Veterano F'],
                'sge_variations': ['Veteranos F', 'Veterans F', 'VETERANOS F'],
                'sort_order': 115,
            },
            {
                'canonical_name': 'veterans-g',
                'arena_variations': ['veterans-g', 'Veterans G', 'Veteranos G', 'VETERANS G', 'Veterano G'],
                'sge_variations': ['Veteranos G', 'Veterans G', 'VETERANOS G'],
                'sort_order': 116,
            },
            {
                'canonical_name': 'veterans-all',
                'arena_variations': ['veterans-all', 'Veterans All', 'Veteranos All', 'VETERANS ALL', 'Veteranos'],
                'sge_variations': ['Veteranos All', 'Veterans All', 'VETERANOS ALL'],
                'sort_order': 117,
            },
            {
                'canonical_name': 'inf-11-12',
                'arena_variations': ['inf-11-12', 'Infantil 11 e 12', 'Infantil 11-12', 'INF-11-12'],
                'sge_variations': ['Infantil 11 e 12', 'Infantil 11-12', 'INF-11-12'],
                'sort_order': 45,
            },
            {
                'canonical_name': 'inf-9-10',
                'arena_variations': ['inf-9-10', 'Infantil 9 e 10', 'Infantil 9-10', 'INF-9-10'],
                'sge_variations': ['Infantil 9 e 10', 'Infantil 9-10', 'INF-9-10'],
                'sort_order': 35,
            },
            {
                'canonical_name': 'inf-7-8',
                'arena_variations': ['inf-7-8', 'Infantil 7 e 8', 'Infantil 7-8', 'INF-7-8'],
                'sge_variations': ['Infantil 7 e 8', 'Infantil 7-8', 'INF-7-8'],
                'sort_order': 25,
            },
            {
                'canonical_name': 'equipes-base',
                'arena_variations': ['equipes-base', 'Equipes Base', 'EQUIPES BASE', 'equipes base'],
                'sge_variations': ['Equipes Base', 'EQUIPES BASE'],
                'sort_order': 200,
            },
            {
                'canonical_name': 'equipes-senior',
                'arena_variations': ['equipes-senior', 'Equipes Senior', 'EQUIPES SENIOR', 'equipes senior'],
                'sge_variations': ['Equipes Senior', 'EQUIPES SENIOR'],
                'sort_order': 201,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for mapping_data in mappings:
            obj, created = AgeGroupMapping.objects.update_or_create(
                canonical_name=mapping_data['canonical_name'],
                defaults={
                    'arena_variations': mapping_data['arena_variations'],
                    'sge_variations': mapping_data['sge_variations'],
                    'sort_order': mapping_data['sort_order'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {obj.canonical_name} → {obj.primary_sge_variation}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {obj.canonical_name} → {obj.primary_sge_variation}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: {created_count} created, {updated_count} updated'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nTotal age group mappings: {AgeGroupMapping.objects.count()}'
            )
        )


