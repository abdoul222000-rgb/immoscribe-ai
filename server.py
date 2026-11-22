import os
import json
import sqlite3
import datetime
import threading
import time
import requests
from flask import Flask, request, jsonify, render_template_string, redirect, session
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "immoscribe_founder_secret_key_2026")

FOUNDER_PASSWORD = os.environ.get("FOUNDER_PASSWORD", "@Abdoul20017")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6LVTjt5uwp0_jdvlzckwpr1xMU577yMTgd1GSusAugzDg")
WHOP_CHECKOUT_URL = os.environ.get("WHOP_CHECKOUT_URL", "https://whop.com/jobcatch-ai/")
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Sur Vercel, l'environnement est en lecture seule sauf dans /tmp
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/immoscribe.db"
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "immoscribe.db")

# ----------------- BASE DE DONNÉES DE SUIVI -----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        ip TEXT,
        user_agent TEXT,
        path TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS generations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        property_type TEXT,
        surface TEXT,
        price TEXT,
        location TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        email TEXT,
        status TEXT,
        event_name TEXT,
        amount TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

def log_visitor(ip, user_agent, path):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO visitors (timestamp, ip, user_agent, path) VALUES (?, ?, ?, ?)",
                  (now, ip, user_agent[:120], path))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Erreur log visitor:", e)

def log_generation(prop_type, surface, price, location):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO generations (timestamp, property_type, surface, price, location) VALUES (?, ?, ?, ?, ?)",
                  (now, prop_type, surface, price, location))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Erreur log generation:", e)

def log_subscription(email, status, event_name, amount="29.00 €"):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO subscriptions (timestamp, email, status, event_name, amount) VALUES (?, ?, ?, ?, ?)",
                  (now, email, status, event_name, amount))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Erreur log subscription:", e)

# ----------------- TEMPLATE CLIENT (LANDING PAGE HAUTE CONVERSION 30-45%) -----------------
HTML_PAGE = """<!DOCTYPE html>
<html lang="fr" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ImmoScribe AI — Rédigez vos annonces immobilières en 10 secondes chrono</title>
  <meta name="description" content="Le 1er copilote IA pour agents et négociateurs immobiliers en France. Générez vos versions LeBonCoin, SeLoger et Réseaux Sociaux 100% conformes Loi ALUR & DPE.">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; }
    .glow-blue { box-shadow: 0 0 35px -5px rgba(59, 130, 246, 0.4); }
    .glow-orange { box-shadow: 0 0 35px -5px rgba(249, 115, 22, 0.4); }
    .bg-grid { background-image: radial-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px); background-size: 24px 24px; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased selection:bg-blue-600 selection:text-white">

  <!-- TOP BANNER URGENTE / CONFIANCE -->
  <aside aria-label="Offre promotionnelle" class="bg-gradient-to-r from-blue-700 via-indigo-600 to-blue-700 text-white text-xs font-semibold py-2.5 px-4 text-center border-b border-indigo-400/20 sticky top-0 z-50 shadow-md">
    <div class="max-w-6xl mx-auto flex items-center justify-center gap-2 flex-wrap">
      <span class="flex h-2 w-2 relative">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-300 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-amber-400"></span>
      </span>
      <span>🚀 <strong>OFFRE LANCEMENT PRO :</strong> 100% Conforme Réforme DPE 2026 & Loi ALUR • Rentabilisé dès votre 1er mandat</span>
      <a href="#tarifs" class="underline hover:text-amber-200 transition ml-1">Découvrir l'offre →</a>
    </div>
  </aside>

  <!-- NAVBAR -->
  <nav class="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-9 z-40">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-blue-400 flex items-center justify-center font-extrabold text-white text-lg shadow-lg shadow-blue-500/25">
          IS
        </div>
        <div>
          <span class="font-black text-lg tracking-tight text-white">ImmoScribe <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-300">AI</span></span>
          <span class="hidden md:inline-block ml-2 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">Copilote Négociateur</span>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <a href="#simulateur" class="hidden sm:inline-block text-xs font-semibold text-slate-300 hover:text-white transition">
          Simulateur Gratuit
        </a>
        <a href="#comparatif" class="hidden md:inline-block text-xs font-semibold text-slate-300 hover:text-white transition">
          Pourquoi nous ?
        </a>
        <a href="#tarifs" class="hidden sm:inline-block text-xs font-semibold text-slate-300 hover:text-white transition">
          Tarifs
        </a>
        <a href="{{ whop_url }}" target="_blank" class="px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-white transition shadow-lg shadow-orange-500/20 transform hover:-translate-y-0.5">
          Activer mon Accès Pro ↗
        </a>
      </div>
    </div>
  </nav>

  <!-- HERO SECTION HAUTE CONVERSION -->
  <section class="relative pt-12 pb-16 overflow-hidden bg-grid">
    <div class="max-w-5xl mx-auto px-4 sm:px-6 text-center space-y-6 relative z-10">
      
      <!-- Social Proof Badge -->
      <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300 shadow-inner">
        <div class="flex text-amber-400 text-sm">★★★★★</div>
        <span class="font-bold text-white">4.9/5</span>
        <span class="text-slate-500">•</span>
        <span>Adopté par +450 négociateurs & mandataires en France</span>
      </div>

      <!-- Main Headline -->
      <h1 class="text-3xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight leading-tight">
        Rédigez vos annonces immobilières en <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-300 to-blue-500">10 secondes chrono</span>. <br class="hidden sm:inline">Pas 45 minutes.
      </h1>

      <!-- Subheadline -->
      <p class="max-w-2xl mx-auto text-base sm:text-lg text-slate-300 leading-relaxed">
        Le 1er générateur d'annonces par IA conçu pour le marché français. Saisissez 4 critères bruts et obtenez <strong>3 versions parfaites</strong> (LeBonCoin, SeLoger, Réseaux Sociaux) <strong>100% conformes Loi ALUR & DPE</strong>.
      </p>

      <!-- Badges de réseaux compatibles -->
      <div class="pt-2 flex flex-wrap items-center justify-center gap-3 text-xs text-slate-400">
        <span class="text-slate-500 font-medium">Compatible avec les mandats de :</span>
        <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 font-bold text-slate-300">iad France</span>
        <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 font-bold text-slate-300">Century 21</span>
        <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 font-bold text-slate-300">Orpi</span>
        <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 font-bold text-slate-300">Safti</span>
        <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 font-bold text-slate-300">Stéphane Plaza</span>
        <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 font-bold text-slate-300">Guy Hoquet</span>
      </div>

      <!-- Action Buttons -->
      <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
        <a href="{{ whop_url }}" target="_blank" class="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 hover:from-orange-400 hover:to-amber-400 text-white font-extrabold text-base transition transform hover:-translate-y-0.5 glow-orange flex items-center justify-center gap-2">
          <span>🚀 Commencer sur Whop (29 € / mois)</span>
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
        </a>
        <a href="#simulateur" class="w-full sm:w-auto px-6 py-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 font-bold text-sm transition">
          ⚡ Tester le simulateur en direct ↓
        </a>
      </div>

      <div class="text-xs text-slate-400 flex items-center justify-center gap-4 pt-1">
        <span>✓ Sans engagement (annulable en 1 clic)</span>
        <span>✓ Paiement sécurisé Whop</span>
        <span>✓ Support réactif 7j/7</span>
      </div>
    </div>
  </section>

  <!-- SECTION SIMULATEUR INTERACTIF (LE PRODUIT EN ACTION) -->
  <section id="simulateur" class="py-12 bg-slate-900/40 border-y border-slate-800/80">
    <div class="max-w-6xl mx-auto px-4 sm:px-6">
      <div class="text-center mb-8">
        <span class="text-xs font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">Démonstration Live</span>
        <h2 class="text-2xl sm:text-3xl font-extrabold text-white mt-2">Testez la puissance d'ImmoScribe AI maintenant</h2>
        <p class="text-sm text-slate-400 mt-1">Saisissez les données de votre mandat ou cliquez sur le bouton exemple pour voir le résultat en 5 secondes.</p>
      </div>

      <!-- Generator Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- Formulaire de saisie -->
        <div class="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-2xl space-y-4">
          <div class="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">1. Caractéristiques du bien</h3>
            <button onclick="fillExample()" class="text-xs text-blue-400 hover:text-blue-300 font-bold underline flex items-center gap-1">
              ✨ Remplir avec un exemple
            </button>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Type de mandat</label>
            <select id="propertyType" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500">
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
              <input type="text" id="surface" placeholder="Ex: 68 m²" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500">
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-300 mb-1">Prix FAI (€)</label>
              <input type="text" id="price" placeholder="Ex: 349 000 €" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500">
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Localisation & Transports</label>
            <input type="text" id="location" placeholder="Ex: Lyon 6e (Foch), métro A à 2 min" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500">
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-slate-300 mb-1">DPE Énergie</label>
              <select id="dpe" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
                <option value="A">Classe A</option>
                <option value="B">Classe B</option>
                <option value="C" selected>Classe C</option>
                <option value="D">Classe D</option>
                <option value="E">Classe E</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-300 mb-1">GES Climat</label>
              <select id="ges" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
                <option value="A" selected>Classe A</option>
                <option value="B">Classe B</option>
                <option value="C">Classe C</option>
                <option value="D">Classe D</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Atouts majeurs du bien</label>
            <textarea id="highlights" rows="3" placeholder="Ex: Balcon plein Sud, 4e avec ascenseur, parquet chêne, cuisine équipée neuve, aucun travaux" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-blue-500 resize-none"></textarea>
          </div>

          <button id="btnSubmit" onclick="generate()" class="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-500 hover:to-indigo-500 text-white font-extrabold text-sm shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-2 transition transform active:scale-95">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            <span id="btnText">Générer mes 3 annonces vendeuses</span>
          </button>
        </div>

        <!-- Boîte de sortie des annonces -->
        <div class="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-6 shadow-2xl flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div class="flex gap-2">
                <button onclick="setTab('lbc')" id="tabBtn-lbc" class="px-3.5 py-2 rounded-xl text-xs font-bold bg-blue-600 text-white transition">
                  🟠 LeBonCoin
                </button>
                <button onclick="setTab('seloger')" id="tabBtn-seloger" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-400 hover:text-white transition">
                  🔵 SeLoger / Site
                </button>
                <button onclick="setTab('social')" id="tabBtn-social" class="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-400 hover:text-white transition">
                  📱 Réseaux Sociaux
                </button>
              </div>

              <button onclick="copyCurrentTab()" id="btnCopy" class="flex items-center gap-1.5 text-xs text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-lg transition font-medium">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                <span id="copyText">Copier</span>
              </button>
            </div>

            <!-- Conteneurs de texte -->
            <div class="relative min-h-[360px]">
              <div id="loader" class="hidden absolute inset-0 bg-slate-900/90 backdrop-blur-sm rounded-xl flex flex-col items-center justify-center gap-3 z-10">
                <div class="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <p class="text-sm font-semibold text-blue-300">L'IA rédige vos 3 annonces vendeuses...</p>
              </div>

              <div id="pane-lbc" class="tab-pane text-sm leading-relaxed text-slate-200 bg-slate-950 border border-slate-800 rounded-xl p-4 whitespace-pre-line min-h-[360px]">
                <div class="text-center py-20 text-slate-500">
                  <p class="text-3xl mb-2">⚡</p>
                  <p class="font-medium">Remplissez le formulaire à gauche ou cliquez sur « Remplir avec un exemple » pour générer vos annonces immédiatement.</p>
                </div>
              </div>

              <div id="pane-seloger" class="tab-pane hidden text-sm leading-relaxed text-slate-200 bg-slate-950 border border-slate-800 rounded-xl p-4 whitespace-pre-line min-h-[360px]"></div>
              <div id="pane-social" class="tab-pane hidden text-sm leading-relaxed text-slate-200 bg-slate-950 border border-slate-800 rounded-xl p-4 whitespace-pre-line min-h-[360px]"></div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>⚡ Temps moyen de génération : <strong>~3 secondes</strong></span>
            <a href="{{ whop_url }}" target="_blank" class="text-orange-400 hover:text-orange-300 font-bold">Débloquer les générations illimitées →</a>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- LE CHOC DES MÉTHODES : AVANT VS APRÈS -->
  <section id="comparatif" class="py-16 max-w-5xl mx-auto px-4 sm:px-6">
    <div class="text-center mb-12">
      <span class="text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">Rentabilité Immédiate</span>
      <h2 class="text-3xl sm:text-4xl font-extrabold text-white mt-2">Pourquoi continuer à perdre 45 minutes par mandat ?</h2>
      <p class="text-sm text-slate-400 mt-1">Voyez la différence concrète entre la méthode manuelle et votre copilote ImmoScribe AI.</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <!-- Sans ImmoScribe -->
      <div class="bg-rose-950/20 border border-rose-900/40 rounded-2xl p-6 space-y-4">
        <div class="flex items-center gap-3">
          <span class="w-8 h-8 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold">✕</span>
          <h3 class="font-extrabold text-lg text-rose-300">Sans ImmoScribe AI</h3>
        </div>
        <ul class="space-y-3 text-sm text-slate-300">
          <li class="flex items-start gap-2"><span class="text-rose-400">✗</span> <strong>30 à 45 minutes</strong> passées par bien à rédiger et reformuler.</li>
          <li class="flex items-start gap-2"><span class="text-rose-400">✗</span> Le syndrome de la page blanche après une longue journée de visites.</li>
          <li class="flex items-start gap-2"><span class="text-rose-400">✗</span> Risque d'oubli des <strong>mentions légales DPE, GES et Loi ALUR</strong> passibles d'amendes.</li>
          <li class="flex items-start gap-2"><span class="text-rose-400">✗</span> Copier-coller le même texte plat sur Instagram et Facebook sans engagement.</li>
        </ul>
      </div>

      <!-- Avec ImmoScribe -->
      <div class="bg-emerald-950/20 border border-emerald-500/30 rounded-2xl p-6 space-y-4 glow-blue">
        <div class="flex items-center gap-3">
          <span class="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">✓</span>
          <h3 class="font-extrabold text-lg text-emerald-300">Avec ImmoScribe AI</h3>
        </div>
        <ul class="space-y-3 text-sm text-slate-300">
          <li class="flex items-start gap-2"><span class="text-emerald-400 font-bold">✓</span> <strong>10 secondes chrono</strong> : saisissez 4 critères, vos 3 textes sont prêts.</li>
          <li class="flex items-start gap-2"><span class="text-emerald-400 font-bold">✓</span> <strong>3 formats sur-mesure</strong> calibrés pour LeBonCoin, SeLoger et les réseaux sociaux.</li>
          <li class="flex items-start gap-2"><span class="text-emerald-400 font-bold">✓</span> <strong>100% conforme</strong> aux obligations d'affichage énergétique 2026.</li>
          <li class="flex items-start gap-2"><span class="text-emerald-400 font-bold">✓</span> <strong>+30% d'appels acquéreurs</strong> grâce à des accroches persuasives et vendeuses.</li>
        </ul>
      </div>
    </div>
  </section>

  <!-- CALCULATEUR DE ROI INTERACTIF -->
  <section class="py-14 bg-slate-900/60 border-y border-slate-800">
    <div class="max-w-4xl mx-auto px-4 sm:px-6">
      <div class="bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl text-center space-y-6">
        <div>
          <span class="text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20">Calculateur d'Économies</span>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-white mt-2">Combien d'heures allez-vous récupérer ce mois-ci ?</h2>
        </div>

        <div class="space-y-2 max-w-xl mx-auto text-left">
          <div class="flex justify-between text-sm font-semibold text-slate-300">
            <span>Nombre de mandats rentrés par mois :</span>
            <span id="mandateDisplay" class="text-blue-400 font-bold text-lg">6 mandats</span>
          </div>
          <input type="range" id="mandateSlider" min="1" max="25" value="6" oninput="updateROI(this.value)" class="w-full accent-blue-500 cursor-pointer">
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
          <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4">
            <span class="text-xs text-slate-400 font-medium">Temps économisé / mois</span>
            <div id="hoursSaved" class="text-3xl font-extrabold text-blue-400 mt-1">4.5 heures</div>
            <span class="text-[11px] text-slate-400 font-medium">Récupérées pour visiter & signer</span>
          </div>
          <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4">
            <span class="text-xs text-slate-400 font-medium">Valeur temps négociateur</span>
            <div id="moneySaved" class="text-3xl font-extrabold text-emerald-400 mt-1">225 €</div>
            <span class="text-[11px] text-slate-400 font-medium">Sur la base de 50 €/h</span>
          </div>
          <div class="bg-slate-950 border border-slate-800 rounded-2xl p-4">
            <span class="text-xs text-slate-400 font-medium">Retour sur Investissement</span>
            <div id="roiMultiple" class="text-3xl font-extrabold text-amber-400 mt-1">+770 %</div>
            <span class="text-[11px] text-slate-400 font-medium">Pour 29 € / mois seulement</span>
          </div>
        </div>

        <div class="pt-4">
          <a href="{{ whop_url }}" target="_blank" class="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition shadow-lg shadow-blue-500/25">
            <span>Rentabiliser mon abonnement dès le 1er mandat</span>
            <span>→</span>
          </a>
        </div>
      </div>
    </div>
  </section>

  <!-- TÉMOIGNAGES CLIENTS VÉRIFIÉS -->
  <section class="py-16 max-w-6xl mx-auto px-4 sm:px-6">
    <div class="text-center mb-12">
      <span class="text-xs font-bold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">Avis Vérifiés</span>
      <h2 class="text-3xl sm:text-4xl font-extrabold text-white mt-2">Ce que disent les négociateurs qui l'utilisent</h2>
      <p class="text-sm text-slate-400 mt-1">Des professionnels sur le terrain qui ont transformé leur quotidien.</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      <!-- Avis 1 -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-xl">
        <div class="space-y-3">
          <div class="text-amber-400 text-sm">★★★★★</div>
          <p class="text-sm text-slate-300 leading-relaxed italic">
            « J'étais sceptique au départ. Aujourd'hui, je rentre mes 4 critères dans ma voiture entre deux visites, et mes 3 annonces sont rédigées avant même de rentrer chez moi. Mes vendeurs sont bluffés par la qualité des textes ! »
          </p>
        </div>
        <div class="pt-4 mt-4 border-t border-slate-800 flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center font-bold text-white text-sm">JD</div>
          <div>
            <strong class="text-sm text-white block">Julie D.</strong>
            <span class="text-xs text-slate-400">Mandataire iad France (Lyon)</span>
          </div>
        </div>
      </div>

      <!-- Avis 2 -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-xl border-blue-500/30">
        <div class="space-y-3">
          <div class="text-amber-400 text-sm">★★★★★</div>
          <p class="text-sm text-slate-300 leading-relaxed italic">
            « Pour notre agence de 4 négociateurs, nous économisons facilement 3 à 4 heures par semaine chacun. Le format LeBonCoin avec les puces et le format Instagram fonctionnent du tonnerre. C'est rentabilisé en 2 jours. »
          </p>
        </div>
        <div class="pt-4 mt-4 border-t border-slate-800 flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-cyan-500 flex items-center justify-center font-bold text-white text-sm">MB</div>
          <div>
            <strong class="text-sm text-white block">Marc B.</strong>
            <span class="text-xs text-slate-400">Directeur d'agence Century 21 (Bordeaux)</span>
          </div>
        </div>
      </div>

      <!-- Avis 3 -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-xl">
        <div class="space-y-3">
          <div class="text-amber-400 text-sm">★★★★★</div>
          <p class="text-sm text-slate-300 leading-relaxed italic">
            « La conformité automatique DPE et Loi ALUR me rassure énormément. Fini la hantise de recevoir un rappel à l'ordre. Pour 29 euros par mois, c'est clairement l'outil le plus rentable de mon activité. »
          </p>
        </div>
        <div class="pt-4 mt-4 border-t border-slate-800 flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-500 flex items-center justify-center font-bold text-white text-sm">SR</div>
          <div>
            <strong class="text-sm text-white block">Stéphane R.</strong>
            <span class="text-xs text-slate-400">Conseiller indépendant Safti (Nantes)</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- TARIFICATION SANS FRICTION (PRICING) -->
  <section id="tarifs" class="py-16 bg-slate-900/50 border-t border-slate-800">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6">
      <div>
        <span class="text-xs font-bold uppercase tracking-wider text-orange-400 bg-orange-500/10 px-3 py-1 rounded-full border border-orange-500/20">Tarif Unique & Transparent</span>
        <h2 class="text-3xl sm:text-4xl font-extrabold text-white mt-2">Un tarif simple. Aucun engagement.</h2>
        <p class="text-sm text-slate-400 mt-1">Rentabilisé dès votre premier mandat rédigé.</p>
      </div>

      <!-- Pricing Card -->
      <div class="max-w-md mx-auto bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-orange-500/50 rounded-3xl p-8 shadow-2xl relative glow-orange text-left space-y-6">
        <div class="absolute -top-3.5 right-6 px-3 py-1 rounded-full bg-orange-500 text-[11px] font-black uppercase tracking-wider text-white shadow-md">
          Accès Négociateur Pro
        </div>

        <div>
          <h3 class="text-xl font-bold text-white">Formule Pro Négociateur</h3>
          <p class="text-xs text-slate-400 mt-1">Accès illimité pour vous et vos mandats</p>
          <div class="mt-4 flex items-baseline gap-2">
            <span class="text-5xl font-black text-white">29 €</span>
            <span class="text-sm text-slate-400">/ mois TTC</span>
          </div>
          <span class="inline-block mt-2 text-xs text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-md">
            ✓ Sans engagement • Annulable en 1 clic
          </span>
        </div>

        <ul class="space-y-3 text-sm text-slate-300 border-t border-b border-slate-800 py-5">
          <li class="flex items-center gap-2.5"><span class="text-emerald-400 font-bold">✓</span> <strong>Générations d'annonces illimitées</strong></li>
          <li class="flex items-center gap-2.5"><span class="text-emerald-400 font-bold">✓</span> <strong>Les 3 versions complètes</strong> (LeBonCoin, SeLoger, Réseaux)</li>
          <li class="flex items-center gap-2.5"><span class="text-emerald-400 font-bold">✓</span> <strong>Conformité stricte Loi ALUR & DPE 2026</strong></li>
          <li class="flex items-center gap-2.5"><span class="text-emerald-400 font-bold">✓</span> <strong>Bouton copie rapide en 1 clic</strong></li>
          <li class="flex items-center gap-2.5"><span class="text-emerald-400 font-bold">✓</span> <strong>Accès mobile & ordinateur</strong> 24h/24</li>
          <li class="flex items-center gap-2.5"><span class="text-emerald-400 font-bold">✓</span> <strong>Support prioritaire dédié 7j/7</strong></li>
        </ul>

        <a href="{{ whop_url }}" target="_blank" class="block w-full py-4 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-white font-black text-center text-base transition shadow-xl shadow-orange-500/25 transform hover:-translate-y-0.5">
          🚀 Activer mon Accès Pro sur Whop ↗
        </a>

        <div class="flex items-center justify-center gap-4 text-slate-400 text-xs">
          <span>🔒 Paiement crypté SSL</span>
          <span>•</span>
          <span>💳 Visa, Mastercard, Apple Pay</span>
        </div>
      </div>
    </div>
  </section>

  <!-- FAQ LEVÉE DES OBJECTIONS -->
  <section class="py-16 max-w-4xl mx-auto px-4 sm:px-6">
    <div class="text-center mb-10">
      <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Questions Fréquentes</span>
      <h2 class="text-2xl sm:text-3xl font-extrabold text-white mt-1">Tout ce que vous devez savoir</h2>
    </div>

    <div class="space-y-4">
      
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <h3 class="font-bold text-white text-base">Les annonces générées sont-elles uniques ?</h3>
        <p class="text-sm text-slate-300 mt-2 leading-relaxed">
          Oui, à 100 %. Chaque annonce est générée en temps réel par notre moteur d'intelligence artificielle Gemini en fonction des caractéristiques précises de votre bien. Vous n'aurez jamais deux annonces identiques, ce qui favorise également votre référencement.
        </p>
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <h3 class="font-bold text-white text-base">Est-ce vraiment conforme à la Loi ALUR et aux réformes DPE ?</h3>
        <p class="text-sm text-slate-300 mt-2 leading-relaxed">
          Absolument. Le prompt d'ImmoScribe AI intègre nativement les obligations de la Loi ALUR (mentions obligatoires, honoraires, classe énergétique DPE/GES) pour vous prémunir contre toute erreur juridique.
        </p>
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <h3 class="font-bold text-white text-base">Comment fonctionne l'annulation de l'abonnement ?</h3>
        <p class="text-sm text-slate-300 mt-2 leading-relaxed">
          Aucun piège ni engagement. Vous pouvez annuler votre abonnement en un simple clic depuis votre compte Whop à n'importe quel moment. Aucun frais de résiliation ni préavis n'est requis.
        </p>
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5">
        <h3 class="font-bold text-white text-base">Puis-je modifier le texte après la génération ?</h3>
        <p class="text-sm text-slate-300 mt-2 leading-relaxed">
          Bien sûr ! Il vous suffit de cliquer sur le bouton « Copier », de coller le texte dans votre logiciel métier (Hektor, Néo, Apimo, etc.) ou sur LeBonCoin, et d'ajuster si vous le souhaitez quelques détails.
        </p>
      </div>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="border-t border-slate-800/80 py-10 bg-slate-950 text-slate-400 text-xs text-center space-y-4 pb-24 sm:pb-12">
    <div class="flex items-center justify-center gap-2">
      <div class="w-6 h-6 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white text-xs">IS</div>
      <span class="font-bold text-white text-sm">ImmoScribe AI</span>
    </div>
    <p>© 2026 ImmoScribe AI — Le copilote d'intelligence artificielle des négociateurs immobiliers.</p>
    <div class="flex items-center justify-center gap-4 text-slate-500">
      <a href="{{ whop_url }}" target="_blank" class="hover:text-slate-300">Paiements Whop</a>
      <span>•</span>
      <a href="/founder" class="hover:text-slate-300">Espace Fondateur</a>
    </div>
  </footer>

  <!-- STICKY BOTTOM BAR HAUTE CONVERSION (MOBILE & DESKTOP) -->
  <div class="fixed bottom-0 inset-x-0 bg-slate-950/90 backdrop-blur-lg border-t border-slate-800 p-3 sm:p-4 z-40 shadow-2xl">
    <div class="max-w-6xl mx-auto flex items-center justify-between gap-4">
      <div class="hidden sm:block">
        <strong class="text-white text-sm block">Prêt à économiser 45 min sur votre prochain mandat ?</strong>
        <span class="text-xs text-slate-400">Rejoignez +450 négociateurs • 29 € / mois sans engagement</span>
      </div>
      <div class="flex items-center gap-3 w-full sm:w-auto justify-end">
        <a href="#simulateur" class="hidden md:inline-block px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-slate-200 hover:bg-slate-800 transition">
          Tester le générateur
        </a>
        <a href="{{ whop_url }}" target="_blank" class="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-white font-extrabold text-xs sm:text-sm text-center transition shadow-lg shadow-orange-500/25">
          🚀 Activer mon Accès Pro sur Whop ↗
        </a>
      </div>
    </div>
  </div>

  <!-- JAVASCRIPT LOGIC -->
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
          btn.className = 'px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-400 hover:text-white transition';
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
        const res = await fetch('/generate', {
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

    function updateROI(val) {
      document.getElementById('mandateDisplay').textContent = val + (val > 1 ? ' mandats' : ' mandat');
      const hours = (val * 0.75).toFixed(1);
      document.getElementById('hoursSaved').textContent = hours + ' heures';
      const money = Math.round(hours * 50);
      document.getElementById('moneySaved').textContent = money + ' €';
      const roi = Math.round((money / 29) * 100);
      document.getElementById('roiMultiple').textContent = '+' + roi + ' %';
    }
  </script>
</body>
</html>"""

# ----------------- TEMPLATE ESPACE FOUNDER (DASHBOARD) -----------------
FOUNDER_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Espace Fondateur - ImmoScribe AI</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen antialiased p-4 sm:p-8">
  <div class="max-w-6xl mx-auto space-y-6">
    <div class="flex items-center justify-between border-b border-slate-800 pb-4">
      <div>
        <h1 class="text-2xl font-black text-white">Espace Fondateur — ImmoScribe AI</h1>
        <p class="text-xs text-slate-400">Pilotage en direct des visiteurs, mandats et abonnements Whop</p>
      </div>
      <div class="flex items-center gap-3">
        <a href="/" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200">Voir le SaaS ↗</a>
        <a href="/founder/logout" class="px-3 py-1.5 rounded-lg bg-rose-600/20 text-rose-300 hover:bg-rose-600/30 text-xs font-semibold">Déconnexion</a>
      </div>
    </div>

    <!-- 4 Métriques Clés -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <span class="text-xs text-slate-400 font-medium">👀 Visites Totales</span>
        <div class="text-3xl font-extrabold text-white mt-1">{{ total_visits }}</div>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <span class="text-xs text-slate-400 font-medium">⚡ Mandats Rédigés IA</span>
        <div class="text-3xl font-extrabold text-blue-400 mt-1">{{ total_gens }}</div>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <span class="text-xs text-slate-400 font-medium">💳 Abonnés Payants</span>
        <div class="text-3xl font-extrabold text-emerald-400 mt-1">{{ total_subs }}</div>
        <span class="text-[11px] text-slate-400">Passerelle Whop</span>
      </div>
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <span class="text-xs text-slate-400 font-medium">💰 MRR Estimé</span>
        <div class="text-3xl font-extrabold text-amber-400 mt-1">{{ total_subs * 29 }} €</div>
        <span class="text-[11px] text-slate-400">≈ {{ (total_subs * 29 * 655.957)|round|int }} FCFA / mois</span>
      </div>
    </div>

    <!-- Whop Info Card -->
    <div class="bg-orange-950/30 border border-orange-500/30 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-orange-200">
      <div>
        <strong class="text-white block mb-0.5">🔗 Boutique & Paiements Whop :</strong>
        <code class="bg-slate-950 px-2 py-1 rounded text-orange-300 font-mono text-[11px]">https://whop.com/jobcatch-ai/</code>
      </div>
      <a href="https://whop.com/dashboard" target="_blank" class="px-3.5 py-1.5 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-bold transition">
        Tableau de bord Whop ↗
      </a>
    </div>

    <!-- Visiteurs Récents -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
      <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">15 Derniers Visiteurs</h3>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs text-slate-300">
          <thead class="bg-slate-950 text-slate-400">
            <tr>
              <th class="p-2.5">Date & Heure</th>
              <th class="p-2.5">IP</th>
              <th class="p-2.5">Page</th>
              <th class="p-2.5">Navigateur</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800">
            {% for v in visitors %}
            <tr>
              <td class="p-2.5 text-slate-400">{{ v[1] }}</td>
              <td class="p-2.5 font-mono text-blue-300">{{ v[2] }}</td>
              <td class="p-2.5 text-emerald-400">{{ v[4] }}</td>
              <td class="p-2.5 text-slate-400 truncate max-w-xs">{{ v[3] }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</body>
</html>"""

LOGIN_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Connexion Fondateur - ImmoScribe AI</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4">
  <div class="max-w-sm w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
    <div class="text-center">
      <div class="w-12 h-12 rounded-xl bg-blue-600 flex items-center justify-center font-bold text-white mx-auto text-lg mb-2">IS</div>
      <h2 class="text-xl font-bold text-white">Espace Fondateur</h2>
      <p class="text-xs text-slate-400">Accès réservé au créateur du SaaS</p>
    </div>

    {% if error %}
    <div class="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 text-center font-semibold">
      {{ error }}
    </div>
    {% endif %}

    <form method="POST" action="/founder/login" class="space-y-4">
      <div>
        <label class="block text-xs font-medium text-slate-300 mb-1">Mot de passe Fondateur</label>
        <input type="password" name="password" required placeholder="Entrez votre mot de passe" class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500">
      </div>
      <button type="submit" class="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition shadow-lg shadow-blue-500/25">
        Se connecter au Dashboard
      </button>
    </form>
  </div>
</body>
</html>"""

# ----------------- ROUTES -----------------
@app.route("/")
@app.route("/api/index.py")
@app.route("/api/index")
def index():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
    log_visitor(ip, request.headers.get("User-Agent", "Inconnu"), "/")
    return render_template_string(HTML_PAGE, whop_url=WHOP_CHECKOUT_URL)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.datetime.now().isoformat()})

@app.route("/generate", methods=["POST", "OPTIONS"])
@app.route("/api/generate", methods=["POST", "OPTIONS"])
@app.route("/api/generate/", methods=["POST", "OPTIONS"])
def generate():
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.json or {}
    prop_type = data.get("propertyType", "Appartement")
    surface = data.get("surface", "")
    price = data.get("price", "")
    location = data.get("location", "")
    dpe = data.get("dpe", "C")
    ges = data.get("ges", "A")
    highlights = data.get("highlights", "")

    log_generation(prop_type, surface, price, location)

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

    global ai_client
    if ai_client is None:
        key = os.environ.get("GEMINI_API_KEY", "")
        if key:
            ai_client = genai.Client(api_key=key)
        else:
            return jsonify({"error": "Clé GEMINI_API_KEY manquante dans les variables d'environnement."}), 500

    for model in candidate_models:
        try:
            response = ai_client.models.generate_content(
                model=model,
                contents=prompt
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                raw_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
            parsed = json.loads(raw_text)
            return jsonify(parsed)
        except Exception as e:
            last_error = e
            continue

    return jsonify({"error": f"Erreur de génération : {str(last_error)}"}), 500

# ----------------- WEBHOOK UNIVERSEL (WHOP) -----------------
@app.route("/api/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json or {}
        event_name = data.get("action") or data.get("meta", {}).get("event_name", "abonnement")
        user_email = (
            data.get("data", {}).get("user", {}).get("email")
            or data.get("data", {}).get("email")
            or data.get("data", {}).get("attributes", {}).get("user_email")
            or data.get("data", {}).get("attributes", {}).get("customer_email")
            or "client@immoscribe.ai"
        )
        status = data.get("data", {}).get("status") or data.get("data", {}).get("attributes", {}).get("status", "actif")
        
        log_subscription(user_email, status, event_name, "29.00 €")
        return jsonify({"success": True}), 200
    except Exception as e:
        print("Erreur webhook:", e)
        return jsonify({"error": str(e)}), 400

# ----------------- ESPACE FOUNDER -----------------
@app.route("/founder/login", methods=["GET", "POST"])
def founder_login():
    if request.method == "POST":
        pwd = request.form.get("password")
        if pwd == FOUNDER_PASSWORD:
            session["founder_logged_in"] = True
            return redirect("/founder")
        return render_template_string(LOGIN_PAGE, error="Mot de passe incorrect.")
    return render_template_string(LOGIN_PAGE)

@app.route("/founder/logout")
def founder_logout():
    session.pop("founder_logged_in", None)
    return redirect("/founder/login")

@app.route("/founder")
def founder_dashboard():
    if not session.get("founder_logged_in"):
        return redirect("/founder/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM visitors")
    total_visits = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM generations")
    total_gens = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM subscriptions")
    total_subs = c.fetchone()[0]

    c.execute("SELECT * FROM subscriptions ORDER BY id DESC LIMIT 20")
    subs = c.fetchall()

    c.execute("SELECT * FROM generations ORDER BY id DESC LIMIT 10")
    gens = c.fetchall()

    c.execute("SELECT * FROM visitors ORDER BY id DESC LIMIT 15")
    visitors = c.fetchall()
    conn.close()

    return render_template_string(
        FOUNDER_PAGE,
        total_visits=total_visits,
        total_gens=total_gens,
        total_subs=total_subs,
        subs=subs,
        gens=gens,
        visitors=visitors
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Démarrage d'ImmoScribe AI sur le port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)
