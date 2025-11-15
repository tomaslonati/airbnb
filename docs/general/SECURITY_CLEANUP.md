# 🚨 SECURITY: SECRETS REMOVED

Este commit sobrescribe cualquier token o secreto que pueda haber sido incluido accidentalmente en commits anteriores.

## Archivos limpiados:

- ✅ `.env.example` - Solo contiene placeholders
- ✅ `config.py` - Solo usa variables de entorno  
- ✅ `tests/simple_test.py` - Solo usa variables de entorno
- ✅ `.env` - Añadido al .gitignore (nunca debería ser commiteado)

## Configuración correcta:

1. **Copia `.env.example` a `.env`**
2. **Completa `.env` con tus credenciales reales**  
3. **`.env` está en `.gitignore` y NO se commitea**

## Tokens removidos:

- AstraDB/DataStax tokens
- Endpoints específicos 
- Credenciales hardcodeadas

Todos los secretos ahora se leen desde variables de entorno de forma segura.