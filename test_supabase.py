#!/usr/bin/env python3
"""
Script de test pour vérifier la connexion à Supabase.

Ce script tente de se connecter à Supabase en utilisant les variables d'environnement
définies et effectue une requête de test.
"""

import os
import sys
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

async def test_supabase_connection():
    """Teste la connexion à Supabase et effectue une requête de test."""
    print("\n" + "="*70)
    print(f"{' Test de Connexion Supabase ':.^70}")
    print("="*70)
    
    # Vérifier les variables d'environnement requises
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\n[ERREUR] Variables d'environnement manquantes :")
        for var in missing_vars:
            print(f"- {var}")
        print("\nAssurez-vous que ces variables sont définies dans le fichier .env")
        return False
    
    print("\n[INFO] Variables d'environnement détectées :")
    for var in required_vars:
        value = os.getenv(var)
        print(f"- {var}: {'définie' if value else 'non définie'}")
        if var == "SUPABASE_SERVICE_KEY" and value:
            print(f"  (longueur: {len(value)} caractères)")
    
    # Tester la connexion à Supabase
    print("\n[TEST] Tentative de connexion à Supabase...")
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        
        print(f"URL: {url}")
        print(f"Clé: {key[:10]}...{key[-10:] if key else ''}")
        
        client = create_client(url, key)
        print("[SUCCÈS] Client Supabase initialisé avec succès")
        
        # Tester une requête simple
        print("\n[TEST] Exécution d'une requête de test...")
        try:
            result = client.table('sources').select("*").limit(1).execute()
            print(f"[SUCCÈS] Connexion à la base de données réussie")
            print(f"- Nombre d'enregistrements dans 'sources': {len(result.data)}")
            
            # Afficher les tables disponibles
            print("\n[INFO] Liste des tables disponibles :")
            try:
                # Cette requête peut ne pas fonctionner selon les permissions
                tables = client.rpc('get_tables', {})
                for table in tables.data:
                    print(f"- {table}")
            except Exception as e:
                print(f"[INFO] Impossible de récupérer la liste des tables (permissions insuffisantes)")
            
            return True
            
        except Exception as e:
            print(f"[ERREUR] Échec de la requête de test: {str(e)}")
            print("\nCauses possibles :")
            print("1. La table 'sources' n'existe pas dans votre base de données")
            print("2. Les permissions de la clé de service sont insuffisantes")
            print("3. La base de données n'est pas accessible")
            return False
            
    except Exception as e:
        print(f"\n[ERREUR] Échec de la connexion à Supabase: {str(e)}")
        print("\nDépannage :")
        print("1. Vérifiez que l'URL de Supabase est correcte")
        print("2. Vérifiez que la clé de service est valide et a les bonnes permissions")
        print("3. Vérifiez que le service Supabase est en cours d'exécution et accessible")
        print("4. Vérifiez les logs de Supabase pour plus de détails")
        return False

if __name__ == "__main__":
    asyncio.run(test_supabase_connection())
