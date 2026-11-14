import os
import json
from flask import Flask, request, jsonify, render_template_string
from google import genai

app = Flask(__name__)

# Récupération sécurisée de la clé Gemini via variable d'environnement (Render)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "CLE_GEMINI_A_DEFINIR")
ai_client = genai.Client(api_key=GEMINI_API_KEY)

HTML_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ImmoScribe AI - Générateur d'Annonces Immobilières</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased">

  <!-- Navbar -->
  <header class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
          IS
        </div>
        <div>
          <span class="font-extrabold text-base tracking-tight text-white">ImmoScribe <span class="text-blue-400">AI</span></span>
          <span class="hidden sm:inline-block ml-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">SaaS Immobilier B2B</span>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div id="trialBadge" class="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Essai gratuit actif (5 jours)</span>
        </div>
        <a id="lemonSubscribeBtn" href="#upgradeModal" onclick="openUpgradeModal()" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition shadow-sm">
          Mon Abonnement
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-6xl mx-auto px-4 sm:px-6 py-8">

    <!-- Top Banner -->
    <div class="mb-8 text-center sm:text-left flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Rédigez vos annonces en 10 secondes chrono</h1>
        <p class="text-sm text-slate-400 mt-1">L'IA génère 3 versions prêtes à publier : LeBonCoin, SeLoger et Réseaux Sociaux.</p>
      </div>
      <div class="flex items-center gap-2 text-xs text-slate-400 bg-slate-900 border border-slate-800 p-2.5 rounded-xl self-center sm:self-auto">
        <span class="text-emerald-400 font-bold">✓</span> Conforme Loi ALUR
        <span class="mx-1 text-slate-700">•</span>
        <span class="text-emerald-400 font-bold">✓</span> Optimisé DPE
      </div>
    </div>

    <!-- Generator Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      
      <!-- Left Column: Input Form -->
      <div class="lg:col-span-5 bg-slate-900/90 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl space-y-4">
        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 class="text-xs font-bold uppercase tracking-wider text-slate-400">Détails du bien</h2>
          <button onclick="fillExample()" class="text-xs text-blue-400 hover:text-blue-300 font-medium">
            Remplir avec un exemple
          </button>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Type de mandat & bien</label>
          <select id="propertyType" class="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition">
            <option value="Vente - Appartement T3">Vente - Appartement T3</option>
            <option value="Vente - Appartement T2">Vente - Appartement T2</option>
            <option value="Vente - Maison individuelle">Vente - Maison individuelle / Villa</option>
            <option value="Vente - Studio investisseur">Vente - Studio investisseur</option>
            <option value="Location - Appartement meublé">Location - Appartement meublé</option>
          </select>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Surface (m²)</label>
            <input type="text" id="surface" placeholder="Ex: 68 m²" class="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition">
          </div>
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Prix FAI (€)</label>
            <input type="text" id="price" placeholder="Ex: 385 000 €" class="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition">
          </div>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Ville / Quartier / Transports</label>
          <input type="text" id="location" placeholder="Ex: Lyon 6e (Foch), métro A à 2 min" class="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition">
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">DPE Énergie</label>
            <select id="dpe" class="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
              <option value="A">Classe A</option>
              <option value="B">Classe B</option>
              <option value="C" selected>Classe C</option>
              <option value="D">Classe D</option>
              <option value="E">Classe E</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">GES Climat</label>
            <select id="ges" class="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
              <option value="A" selected>Classe A</option>
              <option value="B">Classe B</option>
              <option value="C">Classe C</option>
              <option value="D">Classe D</option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-xs font-medium text-slate-300 mb-1">Atouts majeurs du bien</label>
          <textarea id="highlights" rows="3" placeholder="Ex: Balcon plein Sud, 4e avec ascenseur, parquet chêne, cuisine équipée neuve, aucun travaux" class="w-full bg-slate-950 border border-slate-700/80 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-blue-500 transition resize-none"></textarea>
        </div>

        <button id="btnSubmit" onclick="generate()" class="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-500 hover:to-indigo-400 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-2 transition transform active:scale-[0.99]">
          <svg id="sparkleIcon" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
          <span id="btnText">Générer les 3 annonces IA</span>
        </button>
      </div>

      <!-- Right Column: Generated Listings Output -->
      <div class="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col justify-between">
        
        <div>
          <!-- Tab Navigation -->
          <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div class="flex gap-2">
              <button onclick="setTab('lbc')" id="tabBtn-lbc" class="px-3.5 py-2 rounded-xl text-xs font-bold bg-blue-600 text-white transition">
                🟠 LeBonCoin
              </button>
              <button onclick="setTab('seloger')" id="tabBtn-seloger" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800/80 text-slate-400 hover:text-white transition">
                🔵 SeLoger / Site Agence
              </button>
              <button onclick="setTab('social')" id="tabBtn-social" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800/80 text-slate-400 hover:text-white transition">
                📱 Instagram / TikTok
              </button>
            </div>

            <button onclick="copyCurrentTab()" id="btnCopy" class="flex items-center gap-1.5 text-xs text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-lg transition">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
              <span id="copyText">Copier</span>
            </button>
          </div>

          <!-- Output Box -->
          <div class="relative min-h-[350px]">
            <!-- Spinner -->
            <div id="loader" class="hidden absolute inset-0 bg-slate-900/80 backdrop-blur-sm rounded-xl flex flex-col items-center justify-center gap-3 z-10">
              <div class="w-9 h-9 border-3 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <p class="text-xs font-medium text-blue-300">Rédaction par l'IA en cours (Gemini 3.5 Flash)...</p>
            </div>

            <!-- Content Panes -->
            <div id="pane-lbc" class="tab-pane text-sm leading-relaxed text-slate-200 bg-slate-950 border border-slate-800/80 rounded-xl p-4 whitespace-pre-line min-h-[350px]">
              <span class="text-slate-500 italic">Remplissez les informations du mandat à gauche et cliquez sur « Générer les 3 annonces IA » pour obtenir le texte rédigé en direct.</span>
            </div>

            <div id="pane-seloger" class="tab-pane hidden text-sm leading-relaxed text-slate-200 bg-slate-950 border border-slate-800/80 rounded-xl p-4 whitespace-pre-line min-h-[350px]">
            </div>

            <div id="pane-social" class="tab-pane hidden text-sm leading-relaxed text-slate-200 bg-slate-950 border border-slate-800/80 rounded-xl p-4 whitespace-pre-line min-h-[350px]">
            </div>
          </div>
        </div>

        <!-- Footer Value Prop -->
        <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>Temps de rédaction : <strong>~2 secondes</strong></span>
          <span class="text-blue-400">Gagnez jusqu'à 3h par semaine</span>
        </div>

      </div>

    </div>

  </main>

  <!-- Modal Abonnement Lemon Squeezy -->
  <div id="upgradeModal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 text-center space-y-4 shadow-2xl">
      <div class="w-12 h-12 rounded-2xl bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center mx-auto text-xl">
        💳
      </div>
      <h3 class="text-xl font-extrabold text-white">Essai Gratuit de 5 Jours</h3>
      <p class="text-sm text-slate-300">
        Activez votre compte négociateur en renseignant votre carte. 
        <strong>Vous ne payez rien aujourd'hui (0,00 €).</strong>
      </p>

      <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 text-left space-y-2 text-xs">
        <div class="flex justify-between text-slate-300">
          <span>Aujourd'hui :</span>
          <strong class="text-emerald-400">0,00 € (Essai de 5 jours)</strong>
        </div>
        <div class="flex justify-between text-slate-300">
          <span>Après 5 jours :</span>
          <strong>29,00 € / mois</strong>
        </div>
        <div class="flex justify-between text-slate-400 pt-1 border-t border-slate-800">
          <span>Engagement :</span>
          <span>Sans engagement, annulable en 1 clic</span>
        </div>
      </div>

      <!-- Lien vers le checkout Lemon Squeezy configuré -->
      <a id="btnLemonCheckout" href="https://jobcatch-ai.lemonsqueezy.com/checkout/buy/9c606a64-2673-4eed-995e-c502f75811b6" target="_blank" class="block w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition shadow-lg shadow-blue-500/25">
        Commencer l'essai gratuit de 5 jours (Carte requise)
      </a>

      <button onclick="closeUpgradeModal()" class="text-xs text-slate-400 hover:text-white">
        Fermer
      </button>
    </div>
  </div>

  <script>
    let activeTab = 'lbc';

    function setTab(tab) {
      activeTab = tab;
      ['lbc', 'seloger', 'social'].forEach(t => {
        const btn = document.getElementById('tabBtn-' + t);
        const pane = document.getElementById('pane-' + t);
        if (t === tab) {
          btn.className = 'px-3.5 py-2 rounded-xl text-xs font-bold bg-blue-600 text-white transition';
          pane.classList.remove('hidden');
        } else {
          btn.className = 'px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800/80 text-slate-400 hover:text-white transition';
          pane.classList.add('hidden');
        }
      });
    }

    function fillExample() {
      document.getElementById('propertyType').value = 'Vente - Appartement T3';
      document.getElementById('surface').value = '68 m²';
      document.getElementById('price').value = '385 000 €';
      document.getElementById('location').value = 'Paris 15e (Convention), métro ligne 12 à 3 min';
      document.getElementById('dpe').value = 'C';
      document.getElementById('ges').value = 'A';
      document.getElementById('highlights').value = 'Balcon plein Sud sans vis-à-vis, 4e étage avec ascenseur, parquet point de Hongrie, cuisine équipée neuve, copropriété calme avec gardien.';
    }

    async function generate() {
      const propertyType = document.getElementById('propertyType').value;
      const surface = document.getElementById('surface').value;
      const price = document.getElementById('price').value;
      const location = document.getElementById('location').value;
      const dpe = document.getElementById('dpe').value;
      const ges = document.getElementById('ges').value;
      const highlights = document.getElementById('highlights').value;

      if (!surface || !price || !location) {
        alert('Veuillez renseigner au moins la surface, le prix et la localisation.');
        return;
      }

      const loader = document.getElementById('loader');
      const btn = document.getElementById('btnSubmit');
      loader.classList.remove('hidden');
      btn.disabled = true;

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ propertyType, surface, price, location, dpe, ges, highlights })
        });
        const data = await res.json();
        
        if (data.error) {
          alert('Erreur: ' + data.error);
        } else {
          document.getElementById('pane-lbc').textContent = data.leboncoin;
          document.getElementById('pane-seloger').textContent = data.seloger;
          document.getElementById('pane-social').textContent = data.social;
          setTab('lbc');
        }
      } catch (err) {
        alert('Erreur de connexion au serveur.');
      } finally {
        loader.classList.add('hidden');
        btn.disabled = false;
      }
    }

    function copyCurrentTab() {
      const pane = document.getElementById('pane-' + activeTab);
      navigator.clipboard.writeText(pane.textContent.trim());
      const copyText = document.getElementById('copyText');
      copyText.textContent = 'Copié !';
      setTimeout(() => copyText.textContent = 'Copier', 2000);
    }

    function openUpgradeModal() {
      document.getElementById('upgradeModal').classList.remove('hidden');
    }

    function closeUpgradeModal() {
      document.getElementById('upgradeModal').classList.add('hidden');
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json or {}
    prop_type = data.get("propertyType", "Appartement")
    surface = data.get("surface", "")
    price = data.get("price", "")
    location = data.get("location", "")
    dpe = data.get("dpe", "C")
    ges = data.get("ges", "A")
    highlights = data.get("highlights", "")

    prompt = f"""Tu es le meilleur copywriter spécialisé dans l'immobilier français haut de gamme et transaction rapide.
Génère 3 versions d'annonces immobilières vendeuses et conformes pour ce bien :
- Type de bien : {prop_type}
- Surface : {surface}
- Prix de vente : {price}
- Localisation / Transports : {location}
- Performance énergétique : DPE {dpe} / GES {ges}
- Atouts : {highlights}

Format de réponse obligatoire en JSON valide avec exactement ces 3 clés :
{{
  "leboncoin": "Texte percutant pour LeBonCoin : titre en majuscules accrocheur, structure aérée avec puces 'Ce que vous allez aimer', mentions légales DPE obligatoires, appel à réserver une visite.",
  "seloger": "Texte élégant et standing pour SeLoger / site agence : narration soignée, description fluide des pièces, valorisation du quartier et de la vie quotidienne, charges et copropriété.",
  "social": "Post pour Instagram / TikTok / Facebook : phrase d'accroche avec émojis, points clés, appel à l'action immédiat en DM (ex: 'Envoyez VISITE en message privé') et 7 hashtags ciblés."
}}
Réponds STRICTEMENT avec l'objet JSON, sans texte d'introduction ni balises markdown additionnelles."""

    candidate_models = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]
    last_error = None

    for model in candidate_models:
        try:
            response = ai_client.models.generate_content(
                model=model,
                contents=prompt
            )
            raw_text = response.text.strip()
            # Nettoyage si le modèle renvoie des balises ```json
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                raw_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
            
            parsed = json.loads(raw_text)
            return jsonify(parsed)
        except Exception as e:
            last_error = e
            continue

    return jsonify({"error": f"Erreur de génération : {str(last_error)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Démarrage d'ImmoScribe AI sur le port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
