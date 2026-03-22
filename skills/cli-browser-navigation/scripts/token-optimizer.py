#!/usr/bin/env python3
"""
Optimiseur d'utilisation de tokens pour Agent Browser
Analyse et optimise les requêtes pour minimiser l'utilisation de tokens
"""

import json
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import argparse

@dataclass
class TokenStats:
    """Statistiques d'utilisation de tokens"""
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    saved_tokens: int = 0
    optimization_rate: float = 0.0

class TokenOptimizer:
    """Optimiseur de tokens pour la navigation web"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.stats = TokenStats()
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Charge la configuration"""
        default_config = {
            "max_tokens_per_request": 1000,
            "target_compression_ratio": 0.7,
            "remove_patterns": [
                r"<!--.*?-->",  # Commentaires HTML
                r"<script.*?>.*?</script>",  # Scripts
                r"<style.*?>.*?</style>",  # Styles
                r"<nav.*?>.*?</nav>",  # Navigation
                r"<footer.*?>.*?</footer>",  # Pied de page
                r"<header.*?>.*?</header>",  # En-tête
                r"<aside.*?>.*?</aside>",  # Barre latérale
                r"<div class=['\"]ad.*?>.*?</div>",  # Publicités
                r"[\r\n]+",  # Lignes vides multiples
                r"\s{2,}",  # Espaces multiples
            ],
            "keep_patterns": [
                r"<h[1-6].*?>.*?</h[1-6]>",  # Titres
                r"<p.*?>.*?</p>",  # Paragraphes
                r"<article.*?>.*?</article>",  # Articles
                r"<main.*?>.*?</main>",  # Contenu principal
                r"<section.*?>.*?</section>",  # Sections
                r"<ul.*?>.*?</ul>",  # Listes
                r"<ol.*?>.*?</ol>",  # Listes ordonnées
                r"<table.*?>.*?</table>",  # Tableaux
            ],
            "text_optimizations": {
                "remove_redundant_words": True,
                "shorten_long_sentences": True,
                "merge_short_paragraphs": True,
                "extract_key_points": True,
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️  Erreur de chargement config: {e}", file=sys.stderr)
        
        return default_config
    
    def estimate_tokens(self, text: str) -> int:
        """Estime le nombre de tokens dans un texte"""
        # Approximation: 1 token ≈ 4 caractères pour l'anglais
        # Pour le français: 1 token ≈ 3.5 caractères
        return len(text) // 3.5
    
    def optimize_html(self, html: str) -> str:
        """Optimise le HTML pour réduire les tokens"""
        original_tokens = self.estimate_tokens(html)
        
        # Étape 1: Nettoyer le HTML
        cleaned = self._clean_html(html)
        
        # Étape 2: Extraire le contenu pertinent
        extracted = self._extract_relevant_content(cleaned)
        
        # Étape 3: Compresser le texte
        compressed = self._compress_text(extracted)
        
        # Étape 4: Formater pour la sortie
        optimized = self._format_output(compressed)
        
        optimized_tokens = self.estimate_tokens(optimized)
        self.stats.saved_tokens = original_tokens - optimized_tokens
        self.stats.optimization_rate = self.stats.saved_tokens / original_tokens if original_tokens > 0 else 0
        
        return optimized
    
    def _clean_html(self, html: str) -> str:
        """Nettoie le HTML des éléments inutiles"""
        cleaned = html
        
        # Supprimer les patterns configurés
        for pattern in self.config["remove_patterns"]:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # Décoder les entités HTML
        import html
        cleaned = html.unescape(cleaned)
        
        return cleaned.strip()
    
    def _extract_relevant_content(self, html: str) -> str:
        """Extrait le contenu pertinent basé sur les patterns"""
        relevant_parts = []
        
        # Extraire les éléments pertinents
        for pattern in self.config["keep_patterns"]:
            matches = re.findall(pattern, html, flags=re.DOTALL | re.IGNORECASE)
            relevant_parts.extend(matches)
        
        # Si aucun pattern ne correspond, utiliser une heuristique simple
        if not relevant_parts:
            # Extraire le texte entre balises
            text_content = re.sub(r'<[^>]+>', ' ', html)
            # Garder les paragraphes significatifs
            paragraphs = [p.strip() for p in text_content.split('\n\n') if len(p.strip()) > 50]
            relevant_parts = paragraphs[:10]  # Limiter à 10 paragraphes
        
        return '\n\n'.join(relevant_parts)
    
    def _compress_text(self, text: str) -> str:
        """Compresse le texte pour réduire les tokens"""
        if not self.config["text_optimizations"]["extract_key_points"]:
            return text
        
        lines = text.split('\n')
        compressed_lines = []
        
        for line in lines:
            if len(line.strip()) < 10:
                continue  # Ignorer les lignes très courtes
            
            # Appliquer les optimisations configurées
            compressed_line = line
            
            if self.config["text_optimizations"]["remove_redundant_words"]:
                compressed_line = self._remove_redundant_words(compressed_line)
            
            if self.config["text_optimizations"]["shorten_long_sentences"]:
                compressed_line = self._shorten_long_sentences(compressed_line)
            
            compressed_lines.append(compressed_line)
        
        # Fusionner les paragraphes courts si configuré
        if self.config["text_optimizations"]["merge_short_paragraphs"]:
            compressed_text = self._merge_short_paragraphs('\n'.join(compressed_lines))
        else:
            compressed_text = '\n'.join(compressed_lines)
        
        return compressed_text
    
    def _remove_redundant_words(self, text: str) -> str:
        """Supprime les mots redondants"""
        redundant_patterns = [
            (r'\b(en fait|en réalité|à vrai dire|pour ainsi dire)\b', ''),
            (r'\b(très|vraiment|extrêmement|particulièrement)\s+', ''),
            (r'\s+', ' '),  # Espaces multiples
        ]
        
        result = text
        for pattern, replacement in redundant_patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result.strip()
    
    def _shorten_long_sentences(self, text: str) -> str:
        """Raccourcit les phrases trop longues"""
        sentences = re.split(r'[.!?]+', text)
        shortened_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            words = sentence.split()
            if len(words) > 30:  # Phrases de plus de 30 mots
                # Garder le début et la fin
                shortened = ' '.join(words[:15] + ['...'] + words[-10:])
                shortened_sentences.append(shortened)
            else:
                shortened_sentences.append(sentence)
        
        return '. '.join(shortened_sentences) + '.'
    
    def _merge_short_paragraphs(self, text: str) -> str:
        """Fusionne les paragraphes courts"""
        paragraphs = text.split('\n\n')
        merged = []
        current_paragraph = []
        
        for para in paragraphs:
            words = para.split()
            if len(words) < 30:  # Paragraphe court
                current_paragraph.append(para)
            else:
                if current_paragraph:
                    merged.append(' '.join(current_paragraph))
                    current_paragraph = []
                merged.append(para)
        
        if current_paragraph:
            merged.append(' '.join(current_paragraph))
        
        return '\n\n'.join(merged)
    
    def _format_output(self, text: str) -> str:
        """Formate la sortie finale"""
        # Limiter la longueur si nécessaire
        max_tokens = self.config["max_tokens_per_request"]
        current_tokens = self.estimate_tokens(text)
        
        if current_tokens > max_tokens:
            # Tronquer intelligemment
            words = text.split()
            target_words = int(max_tokens * 3.5 / 5)  # Approximation mots/token
            truncated = ' '.join(words[:target_words]) + '... [TRONQUÉ]'
            return truncated
        
        return text
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyse une requête pour l'optimisation"""
        query_tokens = self.estimate_tokens(query)
        
        suggestions = []
        
        # Vérifier la longueur
        if query_tokens > 50:
            suggestions.append({
                "type": "length",
                "message": f"Requête trop longue ({query_tokens} tokens)",
                "suggestion": "Diviser en plusieurs requêtes plus courtes"
            })
        
        # Vérifier la spécificité
        if len(query.split()) < 3:
            suggestions.append({
                "type": "specificity",
                "message": "Requête trop générale",
                "suggestion": "Ajouter des mots-clés spécifiques"
            })
        
        # Vérifier les stop words
        stop_words = ["le", "la", "les", "un", "une", "des", "du", "de", "à"]
        query_words = query.lower().split()
        stop_word_count = sum(1 for word in query_words if word in stop_words)
        
        if stop_word_count > len(query_words) * 0.3:  # Plus de 30% de stop words
            suggestions.append({
                "type": "stop_words",
                "message": f"Trop de mots vides ({stop_word_count}/{len(query_words)})",
                "suggestion": "Supprimer les articles et prépositions inutiles"
            })
        
        return {
            "query": query,
            "tokens": query_tokens,
            "suggestions": suggestions,
            "optimized_query": self._optimize_query(query)
        }
    
    def _optimize_query(self, query: str) -> str:
        """Optimise une requête de recherche"""
        # Supprimer la ponctuation excessive
        optimized = re.sub(r'[.,;:!?]{2,}', ' ', query)
        
        # Supprimer les mots vides courants
        stop_words = {"le", "la", "les", "un", "une", "des", "du", "de", "à", "au", "aux", "dans", "sur", "pour"}
        words = optimized.split()
        filtered_words = [w for w in words if w.lower() not in stop_words]
        
        # Ajouter des opérateurs de recherche si manquants
        if len(filtered_words) > 2 and not any(op in query for op in ['"', 'site:', 'intitle:']):
            # Pour les requêtes complexes, ajouter des guillemets pour les phrases exactes
            if len(filtered_words) >= 4:
                # Trouver des groupes de mots fréquents
                word_pairs = [(filtered_words[i], filtered_words[i+1]) 
                            for i in range(len(filtered_words)-1)]
                # Simple heuristique: mettre entre guillemets les paires les plus longues
                longest_pair = max(word_pairs, key=lambda x: len(x[0]) + len(x[1]))
                idx = filtered_words.index(longest_pair[0])
                filtered_words[idx] = f'"{longest_pair[0]} {longest_pair[1]}"'
                del filtered_words[idx + 1]
        
        return ' '.join(filtered_words)
    
    def generate_report(self) -> str:
        """Génère un rapport d'optimisation"""
        report = [
            "📊 RAPPORT D'OPTIMISATION DE TOKENS",
            "=" * 40,
            f"Tokens économisés: {self.stats.saved_tokens:,}",
            f"Taux d'optimisation: {self.stats.optimization_rate:.1%}",
            "",
            "⚡ CONSEILS POUR ÉCONOMISER DES TOKENS:",
            "1. Utilisez des requêtes spécifiques et concises",
            "2. Limitez la longueur des extractions avec --max-chars",
            "3. Filtrez le contenu avec --select et --exclude",
            "4. Utilisez le cache pour les recherches répétées",
            "5. Privilégiez le format texte au format HTML",
            "",
            "🔧 CONFIGURATION RECOMMANDÉE:",
            f"  max_tokens_per_request: {self.config['max_tokens_per_request']}",
            f"  target_compression_ratio: {self.config['target_compression_ratio']}",
            "",
            "💡 EXEMPLE DE REQUÊTE OPTIMISÉE:",
            "  Avant: 'Quels sont les principes fondamentaux de la physique quantique ?'",
            "  Après: 'principes fondamentaux physique quantique'",
        ]
        
        return '\n'.join(report)

def main():
    parser = argparse.ArgumentParser(description="Optimiseur d'utilisation de tokens pour Agent Browser")
    parser.add_argument("--config", help="Chemin vers le fichier de configuration")
    parser.add_argument("--analyze-query", help="Analyse une requête spécifique")
    parser.add_argument("--optimize-file", help="Optimise un fichier HTML")
    parser.add_argument("--output", help="Fichier de sortie")
    parser.add_argument("--report", action="store_true", help="Génère un rapport")
    
    args = parser.parse_args()
    
    optimizer = TokenOptimizer(args.config)
    
    if args.analyze_query:
        result = optimizer.analyze_query(args.analyze_query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.optimize_file:
        with open(args.optimize_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        optimized = optimizer.optimize_html(html_content)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(optimized)
            print(f"✅ Contenu optimisé sauvegardé dans {args.output}")
            print(f"📊 Tokens économisés: {optimizer.stats.saved_tokens:,}")
        else:
            print(optimized)
    
    elif args.report:
        print(optimizer.generate_report())
    
    else:
        # Mode interactif
        print("🔧 Optimiseur de tokens pour Agent Browser")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Analyser une requête")
            print("2. Optimiser un fichier HTML")
            print("3. Générer un rapport")
            print("4. Quitter")
            
            choice = input("\nVotre choix (1-4): ").strip()
            
            if choice == '1':
                query = input("Entrez la requête à analyser: ").strip()
                result = optimizer.analyze_query(query)
                print("\n📋 Résultat de l'analyse:")
                print(f"  Requête: {result['query']}")
                print(f"  Tokens estimés: {result['tokens']}")
                print(f"  Requête optimisée: {result['optimized_query']}")
                
                if result['suggestions']:
                    print("\n💡 Suggestions:")
                    for suggestion in result['suggestions']:
                        print(f"  - {suggestion['message']}: {suggestion['suggestion']}")
            
            elif choice == '2':
                filepath = input("Chemin du fichier HTML: ").strip()
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    optimized = optimizer.optimize_html(html_content)
                    
                    output_file = input("Fichier de sortie [optimized.html]: ").strip()
                    if not output_file:
                        output_file = "optimized.html"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(optimized)
                    
                    print(f"✅ Fichier optimisé sauvegardé: {output_file}")
                    print(f"📊 Tokens économisés: {optimizer.stats.saved_tokens:,}")
                    print(f"📈 Taux d'optimisation: {optimizer.stats.optimization_rate:.1%}")
            
            elif choice == '3':
                print(optimizer.generate_report())
            
            elif choice == '4':
                print("👋 Au revoir!")
                break
            
            else:
                print("❌ Choix invalide. Veuillez choisir 1-4.")

if __name__ == "__main__":
    main()