import { CLUB } from './club'

// A simple page heading, used until each page's real content is built
export default function PublicPlaceholder({ title, text, children }) {
  return (
    <section className="site-placeholder">
      <div className="site-container">
        <p className="site-eyebrow">{CLUB.name}</p>
        <h1>{title}</h1>
        <p className="site-lead">{text}</p>
        {children}
      </div>
    </section>
  )
}