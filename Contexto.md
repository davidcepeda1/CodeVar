# CodeVAR — Contexto del Proyecto

## Qué es

CodeVAR es un mini error-tracker (rastreador de errores en tiempo de ejecución) inspirado en Sentry, construido específicamente para aplicaciones **FastAPI + Python**. Captura excepciones no manejadas en una aplicación, las agrupa por huella (mismo tipo de excepción + mismo archivo + misma línea), y las expone en un dashboard web con frecuencia, último visto y stack trace.

El nombre "CodeVAR" hace referencia al VAR (Video Assistant Referee) del fútbol: así como el VAR revisa jugadas en busca de faltas, CodeVAR revisa el código en producción en busca de errores.

## Por qué existe este proyecto

Este es un proyecto personal construido por David Cepeda, estudiante de Ingeniería de Software (Universidad de las Fuerzas Armadas ESPE), con dos objetivos:

1. **Aprendizaje técnico real**: entender cómo funciona la observabilidad en producción (captura de excepciones, agrupación/deduplicación de eventos, diseño de APIs de ingesta) construyendo una versión mínima desde cero, en vez de depender únicamente de herramientas cerradas como Sentry.
2. **Proyecto de portafolio**: pieza central para su CV y GitHub al aplicar a prácticas preprofesionales de software en Quito/Sangolquí, Ecuador.

**Importante — framing honesto:** CodeVAR NO pretende competir ni igualar a Sentry. Sentry soporta decenas de lenguajes, agrupación inteligente avanzada, alertas, performance monitoring, session replay, etc. — el trabajo de un equipo grande durante años. CodeVAR es deliberadamente mínimo y de un solo lenguaje (Python/FastAPI). El valor del proyecto no está en "ser mejor que Sentry", está en demostrar comprensión profunda de cómo funciona un sistema de este tipo por dentro.

## Decisiones de alcance ya tomadas

- **Un solo lenguaje/framework**: Python + FastAPI únicamente. No se construirán SDKs para otros lenguajes en esta fase. El formato del evento (JSON) se diseña de forma agnóstica al lenguaje, dejando la puerta abierta a futuros clientes, pero solo se implementa el cliente Python.
- **Fingerprinting simple**: agrupación por `hash(tipo_excepción + archivo + línea)`. Nada de análisis semántico sofisticado tipo Sentry.
- **Dashboard simple**: HTML + Jinja2 server-rendered es suficiente para el MVP. No se requiere React ni frontend separado.
- **Prueba con proyecto real**: el cliente se instalará en `backend-canchas` (proyecto real y ya desplegado) para generar una demo convincente con errores reales, no simulados.

## Arquitectura general

```
Tu app (FastAPI, ej. backend-canchas)
      │  excepción no manejada
      ▼
┌──────────────────┐
│ Middleware/SDK     │  captura excepción + stack trace + contexto
│ (codevar-client)   │  (endpoint, request, timestamp)
└──────────────────┘
      │  POST del evento
      ▼
┌──────────────────┐
│ API de ingesta      │  recibe eventos, calcula fingerprint,
│ (codevar-server)    │  agrupa o crea grupo, guarda evento
└──────────────────┘
      │
      ▼
┌──────────────────┐
│ PostgreSQL           │  proyectos, grupos de error, eventos individuales
└──────────────────┘
      │
      ▼
┌──────────────────┐
│ Dashboard web        │  lista de errores, frecuencia, último visto,
│ (Jinja2)              │  stack trace expandible, marcar resuelto/ignorado
└──────────────────┘
```

## Repositorios

- **`codevar-server`**: API de ingesta + dashboard (FastAPI + PostgreSQL)
- **`codevar-client`**: middleware/SDK instalable vía pip en otros proyectos FastAPI

## Stack técnico

| Capa          | Tecnología                             |
| ------------- | -------------------------------------- |
| Backend / API | FastAPI                                |
| Base de datos | PostgreSQL                             |
| ORM           | SQLAlchemy                             |
| Dashboard     | Jinja2 (server-rendered)               |
| Cliente/SDK   | Paquete Python instalable (`setup.py`) |
| Despliegue    | Render                                 |

## A quién va dirigido este documento

Este archivo, junto a `planning.md`, está pensado como contexto de entrada para Claude Code u otra herramienta de desarrollo asistido, de modo que pueda entender el propósito, las decisiones de alcance ya tomadas, y no proponga expandir el proyecto más allá de lo definido (por ejemplo: no agregar soporte multi-lenguaje, no construir agrupación inteligente avanzada, no agregar autenticación compleja salvo que se indique explícitamente).
