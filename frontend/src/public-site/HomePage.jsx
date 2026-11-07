import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { animate, motion, useInView, useReducedMotion } from 'motion/react'
import { ArrowRight, Clock, ExternalLink, MapPin } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { CLUB, INSTAGRAM_LINK } from './club'
import InstagramIcon from './InstagramIcon'
import Reveal from './Reveal'
import heroPhoto from '../assets/photos/hero/home-hero.webp'
import aboutPhoto from '../assets/photos/sections/about.webp'
import activitiesPhoto from '../assets/photos/sections/activities.webp'
import membershipPhoto from '../assets/photos/sections/membership.webp'

// Every photo in the belt folder, found automatically and sorted by file name
const BELT_PHOTOS = Object.entries(
  import.meta.glob('../assets/photos/belt/*.{webp,jpg,jpeg,png}', { eager: true, import: 'default' })
)
  .sort(([a], [b]) => a.localeCompare(b))
  .map(([path, url]) => ({ url, alt: photoName(path) }))

// "../assets/photos/belt/02-deep-in-thought.webp" -> "Deep in thought"
function photoName(path) {
  const words = path.split('/').pop().replace(/\.\w+$/, '').replace(/^\d+-/, '').replace(/-/g, ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

// A smooth "ease out" curve: starts quickly, then settles gently
const SMOOTH = [0.22, 1, 0.36, 1]

const FOUNDED = 2016

// The highlight figures. Those with a number count up when they scroll into view.
const HIGHLIGHTS = [
  { number: new Date().getFullYear() - FOUNDED, label: 'Years of bringing chess players together' },
  { number: 200, suffix: '+', label: 'Players at our largest tournaments' },
  { number: 2, label: 'Club days every week: Friday & Saturday' },
  { text: 'FIDE', label: 'Certified arbiters on our team' },
]

// The three sections that lead to the other pages. They zigzag: photo left, right, left.
const SECTIONS = [
  {
    photo: aboutPhoto,
    alt: 'The KICA team standing beside the club banner',
    eyebrow: 'About KICA',
    title: 'A Passion for Chess. A Community for Everyone.',
    text:
      'For ten years, our volunteers have been bringing chess lovers together in Kuwait. ' +
      'Get to know the people, the history and the spirit behind the club.',
    button: 'About Us',
    to: '/about',
  },
  {
    photo: activitiesPhoto,
    alt: 'Players at a large KICA tournament in a grand hall',
    eyebrow: 'Activities & Tournaments',
    title: 'From Weekly Games to Major Tournaments',
    text:
      'Friday and Saturday club sessions, tournaments with 200+ players, lectures and ' +
      'simultaneous games with Grandmasters, and plenty more happening at KICA.',
    button: 'Check It Out',
    to: '/activities',
  },
  {
    photo: membershipPhoto,
    alt: 'Young prize winners holding their trophies with the KICA team',
    eyebrow: 'Membership',
    title: 'Join the KICA Family',
    text:
      'Your next move starts here. A welcoming club for children, adults and families, ' +
      'from beginners to tournament players.',
    button: 'Join the Club',
    to: '/membership',
  },
]

export default function HomePage() {
  return (
    <>
      <Hero />
      <Welcome />
      <PhotoBelt />
      {SECTIONS.map((section, index) => (
        <FeatureSection key={section.to} {...section} photoOnRight={index % 2 === 1} />
      ))}
    </>
  )
}

/* ---------- 1. Hero: logo, name and buttons on the left, the big photo on the right ---------- */

function Hero() {
  return (
    <section className="home-hero">
      <div className="site-container home-hero-inner">
        {/* The text side: logo (in full colour), name, subtitle and buttons */}
        <motion.div
          className="home-hero-text"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: SMOOTH }}
        >
          <img src="/kica-logo.png" alt="" className="home-hero-logo" />
          <h1>{CLUB.name}</h1>
          <p className="home-hero-subtitle">Bringing Chess Enthusiasts Together Since {FOUNDED}</p>

          <div className="home-hero-buttons">
            <Link to="/membership" className="site-button">
              Join Our Chess Community
              <ArrowRight size={18} aria-hidden="true" />
            </Link>
            <Link to="/activities" className="site-button-outline">
              Explore Our Activities
            </Link>
          </div>
        </motion.div>

        {/* The photo side: black & white with the maroon tint (site-photo) */}
        <motion.div
          className="home-hero-photo site-photo"
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, delay: 0.1, ease: SMOOTH }}
        >
          <img
            src={heroPhoto}
            alt="Young players concentrating on their games at a KICA tournament"
            fetchPriority="high"
          />
        </motion.div>
      </div>
    </section>
  )
}

/* ---------- 2. Welcome text and the highlight figures ---------- */
function Welcome() {
  return (
    <section className="home-welcome">
      <div className="site-container">
        <div className="home-welcome-inner">
          <Reveal className="home-welcome-text">
            <p>
              Welcome to the Kuwait Indian Chess Association (KICA), a community-driven sports
              association dedicated to promoting chess and connecting players across Kuwait.
            </p>
            <p>
              Whether you are discovering chess for the first time, developing your competitive
              skills, or simply enjoying the game, KICA offers a friendly and inclusive environment
              for players of all nationalities, ages, and skill levels.
            </p>
          </Reveal>

          <Reveal className="home-location" delay={0.15}>
            <div className="home-location-details">
              <p className="site-eyebrow">Visit Us</p>
              <p className="home-location-line">
                <MapPin size={20} aria-hidden="true" />
                <span>
                  <strong>{CLUB.address}</strong>
                  <span className="home-location-landmark">{CLUB.landmark}</span>
                </span>
              </p>
              {CLUB.timings.map((timing) => (
                <p key={timing.label} className="home-location-line">
                  <Clock size={20} aria-hidden="true" />
                  <span>
                    <strong>{timing.label}:</strong>
                    <span className="home-location-time">{timing.time}</span>
                  </span>
                </p>
              ))}
              <p className="home-location-line">
                <InstagramIcon size={20} />
                <a href={INSTAGRAM_LINK} target="_blank" rel="noopener noreferrer">
                  @{CLUB.instagram}
                </a>
              </p>
              <a
                href={CLUB.mapsLink}
                target="_blank"
                rel="noopener noreferrer"
                className="site-button home-location-button"
              >
                Open in Google Maps
                <ExternalLink size={18} aria-hidden="true" />
              </a>
            </div>

            <div className="home-location-qrs">
              <div className="home-location-qr">
                <QRCodeSVG value={CLUB.mapsLink} size={112} />
                <span>Scan for directions</span>
              </div>
              <div className="home-location-qr">
                <QRCodeSVG value={INSTAGRAM_LINK} size={112} />
                <span>Follow us on Instagram</span>
              </div>
            </div>
          </Reveal>
        </div>

        <div className="home-highlights">
          {HIGHLIGHTS.map((highlight, index) => (
            <motion.div
              key={highlight.label}
              className="home-highlight"
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 'some' }}
              transition={{ duration: 0.6, delay: index * 0.1, ease: SMOOTH }}
            >
              <strong>
                {highlight.number !== undefined ? (
                  <CountUp to={highlight.number} suffix={highlight.suffix} />
                ) : (
                  highlight.text
                )}
              </strong>
              <span>{highlight.label}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
// A number that counts up from 0 the first time it scrolls into view
function CountUp({ to, suffix = '' }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, amount: 0.6 })
  const reduceMotion = useReducedMotion()
  const [shown, setShown] = useState(0)

  useEffect(() => {
    // Only count when it's on screen, and not for people with "reduce motion" on
    if (!inView || reduceMotion) {
      return
    }

    const counting = animate(0, to, {
      duration: 1.6,
      ease: 'easeOut',
      onUpdate: (value) => setShown(Math.round(value)),
    })

    return () => counting.stop()
  }, [inView, reduceMotion, to])

  // "Reduce motion" on: just show the final number, without counting
  const value = reduceMotion ? to : shown

  return (
    <span ref={ref}>
      {value}
      {suffix}
    </span>
  )
}

/* ---------- 3. The photo belt: photos sliding slowly across the screen ---------- */

// The photos are shown 3 times in a row. The strip slides left by exactly one set,
// then starts again, so the loop never shows a jump or a gap.
const BELT_COPIES = 3

function PhotoBelt() {
  if (BELT_PHOTOS.length === 0) {
    return null
  }

  return (
    <motion.section
      className="home-belt"
      aria-label="Photos from KICA events"
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, amount: 'some' }}
      transition={{ duration: 0.8 }}
    >
      <div
        className="home-belt-track"
        style={{ '--belt-duration': `${BELT_PHOTOS.length * 4.3}s` }}
      >
        {Array.from({ length: BELT_COPIES }, (_, copy) =>
          BELT_PHOTOS.map((photo) => (
            <div key={`${copy}-${photo.url}`} className="home-belt-item site-photo" aria-hidden={copy > 0}>
              <img src={photo.url} alt={copy === 0 ? photo.alt : ''} loading="lazy" />
            </div>
          ))
        )}
      </div>
    </motion.section>
  )
}

/* ---------- 4–6. About, Activities and Membership: photo + text + button ---------- */

function FeatureSection({ photo, alt, eyebrow, title, text, button, to, photoOnRight }) {
  return (
    <section className={photoOnRight ? 'home-feature photo-right' : 'home-feature'}>
      <div className="site-container home-feature-inner">
        <motion.div
          className="home-feature-photo site-photo"
          initial={{ opacity: 0, x: photoOnRight ? 60 : -60 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, amount: 'some' }}
          transition={{ duration: 0.8, ease: SMOOTH }}
        >
          <img src={photo} alt={alt} loading="lazy" />
        </motion.div>

        <motion.div
          className="home-feature-text"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 'some' }}
          transition={{ duration: 0.8, delay: 0.15, ease: SMOOTH }}
        >
          <p className="site-eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
          <p className="site-lead">{text}</p>
          <Link to={to} className="site-button">
            {button}
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        </motion.div>
      </div>
    </section>
  )
}