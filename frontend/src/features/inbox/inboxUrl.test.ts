import { describe, expect, it } from 'vitest'

import { inboxSearch, parseInboxParams, resolveView } from './inboxUrl'

const parse = (query: string) => parseInboxParams(new URLSearchParams(query))

describe('parseInboxParams', () => {
  it('sin parámetros no elige vista', () => {
    expect(parse('')).toEqual({ view: null, status: null })
  })

  it('un estado implica la vista Todas', () => {
    expect(parse('estado=detenida')).toEqual({ view: 'all', status: 'BLOCKED' })
  })

  it('pendiente es la vista Por decidir, no un filtro de Todas', () => {
    expect(parse('estado=pendiente')).toEqual({ view: 'pending', status: null })
  })

  it('entiende las URLs antiguas con códigos de la API', () => {
    expect(parse('vista=todas&estado=PENDING_APPROVAL')).toEqual({ view: 'pending', status: null })
    expect(parse('vista=todas&estado=DRAFT_READY')).toEqual({ view: 'all', status: 'DRAFT_READY' })
  })

  it('ignora valores desconocidos', () => {
    expect(parse('vista=otra&estado=xyz')).toEqual({ view: null, status: null })
  })
})

describe('resolveView', () => {
  it('sin elección abre la cola si hay pendientes, y Todas si no', () => {
    expect(resolveView({ view: null, status: null }, 2, false)).toBe('pending')
    expect(resolveView({ view: null, status: null }, 0, false)).toBe('all')
  })

  it('respeta la vista elegida', () => {
    expect(resolveView({ view: 'all', status: null }, 2, false)).toBe('all')
  })
})

describe('inboxSearch', () => {
  it('escribe el estado en minúsculas y sin vista redundante', () => {
    expect(inboxSearch({ view: 'all', status: 'DRAFT_READY' })).toEqual({ estado: 'borrador-listo' })
  })

  it('una pestaña elegida queda escrita', () => {
    expect(inboxSearch({ view: 'pending', status: null })).toEqual({ vista: 'por-decidir' })
    expect(inboxSearch({ view: 'all', status: null })).toEqual({ vista: 'todas' })
  })

  it('sin elección no escribe nada', () => {
    expect(inboxSearch({ view: null, status: null })).toEqual({})
  })

  it('elegir Pendiente en el filtro lleva a Por decidir', () => {
    expect(inboxSearch({ view: 'all', status: 'PENDING_APPROVAL' })).toEqual({ vista: 'por-decidir' })
  })

  it('reescribe la URL antigua a la forma canónica', () => {
    const legacy = parseInboxParams(new URLSearchParams('vista=todas&estado=BLOCKED'))
    expect(inboxSearch(legacy)).toEqual({ estado: 'detenida' })
  })
})
