export default function BackupPage() {
  return (
    <section className="card">
      <h2>Download club data</h2>
      <p className="hint">
        An Excel copy of everything in the app: players, monthly fees, payments, expenses,
        transfers, attendance and opening balances. Keep it somewhere safe, for example in the
        club's shared drive, so the club always has its records even if the website is down.
      </p>
      <p className="hint">
        The file contains members' payment details, so please don't share it outside the
        committee.
      </p>
      <br></br>
      <div className="actions">
        <a className="button" href="/api/exports/club-data">
          Download club data (Excel)
        </a>
      </div>
    </section>
  )
}