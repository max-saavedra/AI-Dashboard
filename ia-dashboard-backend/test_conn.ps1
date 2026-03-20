# Opción A: Usando el módulo de python (Recomendado)
python -m scripts.test_auth

# Opción B: Forzando el PYTHONPATH
$env:PYTHONPATH="."
python scripts/test_auth.py