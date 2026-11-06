import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import Reveal from './Reveal'

// The maroon band at the end of a page.
// "to" is a page on our site (e.g. /membership); "href" is anything else, e.g. an email link.
export default function JoinBand({
  title = 'Ready to make your move?',
  text = 'Join a welcoming chess community for players of all ages and abilities.',
  button = 'Become a Member',
  to = '/membership',
  href,
}) {
  const content = (
    <>
      {button}
      <ArrowRight size={18} aria-hidden="true" />
    </>
  )

  return (
    <section className="join-band">
      <div className="site-container">
        <Reveal className="join-band-inner">
          <div>
            <h2>{title}</h2>
            <p>{text}</p>
          </div>
          {href ? (
            <a href={href} className="join-band-button">
              {content}
            </a>
          ) : (
            <Link to={to} className="join-band-button">
              {content}
            </Link>
          )}
        </Reveal>
      </div>
    </section>
  )
}