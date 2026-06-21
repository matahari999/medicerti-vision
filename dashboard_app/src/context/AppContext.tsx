import { createContext, useCallback, useContext, useReducer, useRef } from "react"
import type { DetectionEvent, EventStats } from "../types"

interface AppState {
  events: DetectionEvent[]
  stats: EventStats
  connected: boolean
}

type Action =
  | { type: 'ADD_EVENT'; event: DetectionEvent }
  | { type: 'SET_CONNECTED'; connected: boolean }
  | { type: 'CLEAR_EVENTS' }

const initialState: AppState = {
  events: [],
  stats: { fall: 0, elopement: 0, loitering: 0, stranger: 0 },
  connected: false,
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'ADD_EVENT': {
      const ev = action.event
      return {
        ...state,
        events: [ev, ...state.events].slice(0, 500),
        stats: {
          ...state.stats,
          [ev.event_type]: (state.stats[ev.event_type as keyof EventStats] ?? 0) + 1,
        },
      }
    }
    case 'SET_CONNECTED':
      return { ...state, connected: action.connected }
    case 'CLEAR_EVENTS':
      return { ...state, events: [], stats: { fall: 0, elopement: 0, loitering: 0, stranger: 0 } }
    default:
      return state
  }
}

const StateCtx = createContext<AppState>(initialState)
const DispatchCtx = createContext<(action: Action) => void>(() => {})

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const idRef = useRef(0)

  const addEvent = useCallback((raw: Omit<DetectionEvent, 'id'>) => {
    dispatch({ type: 'ADD_EVENT', event: { ...raw, id: ++idRef.current } })
  }, [])

  const wrappedDispatch = useCallback((action: Action) => {
    if (action.type === 'ADD_EVENT') addEvent(action.event)
    else dispatch(action)
  }, [addEvent])

  return (
    <StateCtx.Provider value={state}>
      <DispatchCtx.Provider value={wrappedDispatch}>
        {children}
      </DispatchCtx.Provider>
    </StateCtx.Provider>
  )
}

export const useAppState = () => useContext(StateCtx)
export const useAppDispatch = () => useContext(DispatchCtx)
