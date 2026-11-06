import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import Reveal from './Reveal'

// The maroon band at the end of a page, inviting people to become members
export default function JoinBand({
  title = 'Ready to make your move?',
  text = 'Join a welcoming chess community for players of all ages and abilities.',
  button = 'Become a Member',
  to = '/membership',
}) {
  return (
    <section className="join-band">
      <div className="site-container">
        <Reveal className="join-band-inner">
          <div>
            <h2>{title}</h2>
            <p>{text}</p>
          </div>
          <Link to={to} className="join-band-button">
            {button}
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </Reveal>
      </div>
    </section>
  )
}