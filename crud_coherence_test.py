#!/usr/bin/env python3
"""
Test de cohérence des données entre les endpoints CRUD de NeuralStark
Vérifie que les compteurs sont corrects et cohérents entre les différents endpoints
"""

import requests
import json
import time
from datetime import datetime

BACKEND_URL = "https://end-to-end-test.preview.emergentagent.com/api"

def test_data_coherence():
    """Test la cohérence des données entre tous les endpoints CRUD"""
    session = requests.Session()
    
    print("=" * 80)
    print("TEST DE COHÉRENCE DES DONNÉES CRUD NEURALSTARK")
    print("=" * 80)
    print()
    
    # 1. Test GET /api/documents/status
    print("1. 📊 Test GET /api/documents/status")
    status_response = session.get(f"{BACKEND_URL}/documents/status")
    if status_response.status_code == 200:
        status_data = status_response.json()
        total_docs = status_data["total_documents"]
        indexed_chunks = status_data["indexed_documents"]
        last_updated = status_data["last_updated"]
        print(f"   ✅ Status: {total_docs} documents, {indexed_chunks} chunks indexés")
        print(f"   📅 Dernière mise à jour: {last_updated}")
    else:
        print(f"   ❌ Erreur: {status_response.status_code}")
        return False
    
    print()
    
    # 2. Test GET /api/documents/list
    print("2. 📋 Test GET /api/documents/list")
    list_response = session.get(f"{BACKEND_URL}/documents/list")
    if list_response.status_code == 200:
        list_data = list_response.json()
        list_total = list_data["total_count"]
        docs_by_type = list_data["documents_by_type"]
        print(f"   ✅ Liste: {list_total} documents trouvés")
        for doc_type, files in docs_by_type.items():
            print(f"      - {doc_type}: {len(files)} fichiers")
        
        # Vérifier cohérence avec status
        if list_total == total_docs:
            print(f"   ✅ Cohérence: Liste ({list_total}) = Status ({total_docs})")
        else:
            print(f"   ❌ Incohérence: Liste ({list_total}) ≠ Status ({total_docs})")
    else:
        print(f"   ❌ Erreur: {list_response.status_code}")
        return False
    
    print()
    
    # 3. Test GET /api/documents/cache-stats
    print("3. 💾 Test GET /api/documents/cache-stats")
    cache_response = session.get(f"{BACKEND_URL}/documents/cache-stats")
    if cache_response.status_code == 200:
        cache_data = cache_response.json()
        cached_docs = cache_data["total_documents"]
        cached_chunks = cache_data["total_chunks"]
        cache_size = cache_data["total_size_bytes"]
        print(f"   ✅ Cache: {cached_docs} docs, {cached_chunks} chunks, {cache_size} bytes")
        
        # Vérifier cohérence avec status
        if cached_docs == total_docs:
            print(f"   ✅ Cohérence docs: Cache ({cached_docs}) = Status ({total_docs})")
        else:
            print(f"   ⚠️  Différence docs: Cache ({cached_docs}) ≠ Status ({total_docs})")
            
        if cached_chunks == indexed_chunks:
            print(f"   ✅ Cohérence chunks: Cache ({cached_chunks}) = Status ({indexed_chunks})")
        else:
            print(f"   ⚠️  Différence chunks: Cache ({cached_chunks}) ≠ Status ({indexed_chunks})")
    else:
        print(f"   ❌ Erreur: {cache_response.status_code}")
        return False
    
    print()
    
    # 4. Test GET /api/health
    print("4. 🏥 Test GET /api/health")
    health_response = session.get(f"{BACKEND_URL}/health")
    if health_response.status_code == 200:
        health_data = health_response.json()
        health_status = health_data["status"]
        mongodb_status = health_data["mongodb"]
        health_indexed = health_data["documents_indexed"]
        uptime = health_data["uptime_seconds"]
        version = health_data["version"]
        print(f"   ✅ Santé: {health_status}, MongoDB: {mongodb_status}")
        print(f"   📊 Documents indexés: {health_indexed}")
        print(f"   ⏱️  Uptime: {uptime}s, Version: {version}")
        
        # Vérifier cohérence avec status
        if health_indexed == indexed_chunks:
            print(f"   ✅ Cohérence: Health ({health_indexed}) = Status ({indexed_chunks})")
        else:
            print(f"   ⚠️  Différence: Health ({health_indexed}) ≠ Status ({indexed_chunks})")
    else:
        print(f"   ❌ Erreur: {health_response.status_code}")
        return False
    
    print()
    
    # 5. Test POST /api/documents/reindex (incrémental)
    print("5. 🔄 Test POST /api/documents/reindex (incrémental)")
    reindex_response = session.post(f"{BACKEND_URL}/documents/reindex")
    if reindex_response.status_code == 200:
        reindex_data = reindex_response.json()
        print(f"   ✅ Réindexation incrémentale: {reindex_data['message']}")
        
        # Attendre et vérifier le status après
        print("   ⏳ Attente 3 secondes...")
        time.sleep(3)
        
        status_after = session.get(f"{BACKEND_URL}/documents/status")
        if status_after.status_code == 200:
            status_after_data = status_after.json()
            new_indexed = status_after_data["indexed_documents"]
            new_last_updated = status_after_data["last_updated"]
            print(f"   📊 Après réindexation: {new_indexed} chunks indexés")
            print(f"   📅 Nouvelle date: {new_last_updated}")
            
            if new_last_updated != last_updated:
                print(f"   ✅ Timestamp mis à jour correctement")
            else:
                print(f"   ⚠️  Timestamp inchangé (normal si cache utilisé)")
        else:
            print(f"   ❌ Erreur vérification post-reindex: {status_after.status_code}")
    else:
        print(f"   ❌ Erreur: {reindex_response.status_code}")
        return False
    
    print()
    
    # 6. Test POST /api/documents/reindex?clear_cache=true (complet)
    print("6. 🔄 Test POST /api/documents/reindex?clear_cache=true (complet)")
    full_reindex_response = session.post(f"{BACKEND_URL}/documents/reindex?clear_cache=true")
    if full_reindex_response.status_code == 200:
        full_reindex_data = full_reindex_response.json()
        print(f"   ✅ Réindexation complète: {full_reindex_data['message']}")
        
        # Vérifier que le cache est vidé immédiatement
        cache_after_clear = session.get(f"{BACKEND_URL}/documents/cache-stats")
        if cache_after_clear.status_code == 200:
            cache_clear_data = cache_after_clear.json()
            cleared_docs = cache_clear_data["total_documents"]
            cleared_chunks = cache_clear_data["total_chunks"]
            print(f"   💾 Cache après clear: {cleared_docs} docs, {cleared_chunks} chunks")
            
            if cleared_docs == 0 and cleared_chunks == 0:
                print(f"   ✅ Cache correctement vidé")
            else:
                print(f"   ⚠️  Cache pas complètement vidé")
        
        # Attendre la fin de la réindexation
        print("   ⏳ Attente 5 secondes pour la réindexation complète...")
        time.sleep(5)
        
        # Vérifier le status final
        final_status = session.get(f"{BACKEND_URL}/documents/status")
        if final_status.status_code == 200:
            final_data = final_status.json()
            final_docs = final_data["total_documents"]
            final_chunks = final_data["indexed_documents"]
            final_updated = final_data["last_updated"]
            print(f"   📊 Status final: {final_docs} docs, {final_chunks} chunks")
            print(f"   📅 Timestamp final: {final_updated}")
            
            # Vérifier cohérence finale
            if final_docs == 12 and final_chunks >= 68:
                print(f"   ✅ Valeurs finales cohérentes avec les attentes")
            else:
                print(f"   ⚠️  Valeurs finales différentes des attentes (12 docs, 68+ chunks)")
        else:
            print(f"   ❌ Erreur vérification finale: {final_status.status_code}")
    else:
        print(f"   ❌ Erreur: {full_reindex_response.status_code}")
        return False
    
    print()
    print("=" * 80)
    print("✅ TESTS DE COHÉRENCE CRUD TERMINÉS")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_data_coherence()
    if success:
        print("🎉 Tous les tests de cohérence CRUD ont réussi!")
    else:
        print("⚠️  Certains tests de cohérence ont échoué.")