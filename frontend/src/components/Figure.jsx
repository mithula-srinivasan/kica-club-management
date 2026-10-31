export default function Figure({ label, value }) {
  return (
    <div className="figure">
      <span className="stat-label">{label}</span>
      <strong>{value}</strong>
    </div>
  )
}