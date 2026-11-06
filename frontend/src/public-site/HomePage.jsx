import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { ArrowRight } from 'lucide-react'
import { CLUB } from './club'

// A smooth "ease out" curve: starts quickly, then settles gently
const SMOOTH = [0.22, 1, 0.36, 1]

export default function HomePage() {
  return (
    <section className="home-hero">
      <div className="site-container home-hero-inner">
        <motion.img
          src="/kica-logo.png"
          alt="Kuwait Indian Chess Association logo"
          className="home-hero-logo"
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: SMOOTH }}
        />

        <motion.div
          className="home-hero-text"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.15, ease: SMOOTH }}
        >
          <p className="site-eyebrow">Since 2006</p>
          <h1>{CLUB.name}</h1>
          <p className="home-hero-tagline">{CLUB.tagline}</p>
          <Link to="/membership" className="site-button">
            Join KICA
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </motion.div>
      </div>
    </section>
  )
}