import { useCallback, useEffect, useState } from "react"

function getHash(): string {
  const hash = window.location.hash.replace(/^#/, "")
  return hash.startsWith("/") ? hash : "/" + hash
}

export function useHashLocation(): [string, (to: string) => void] {
  const [location, setLocation] = useState(getHash)

  useEffect(() => {
    const handler = () => setLocation(getHash())
    window.addEventListener("hashchange", handler)
    return () => window.removeEventListener("hashchange", handler)
  }, [])

  const navigate = useCallback((to: string) => {
    window.location.hash = to
  }, [])

  return [location, navigate]
}
