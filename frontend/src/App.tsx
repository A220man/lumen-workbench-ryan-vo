import React from "react"
import { Link } from "react-router-dom"

export default function App() {
  return (
    <div className="App">
      <nav>
        <Link to="/">Home</Link>
        <Link to="/titles">Titles</Link>
        <Link to="/evaluations">Evaluations</Link>
      </nav>
      <h1>Lumen Workbench</h1>
      <p>AI/ML developer tools for PS5 executable porting analysis</p>
    </div>
  )
}