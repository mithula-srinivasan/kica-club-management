import { motion } from 'motion/react'
import { Armchair, BookOpen, Monitor, MapPin, Presentation, Quote, Scale, Timer } from 'lucide-react'
import { CLUB } from './club'
import JoinBand from './JoinBand'
import PageIntro from './PageIntro'
import Reveal, { SMOOTH } from './Reveal'
import teamPhoto from '../assets/photos/sections/about.webp'

// The facilities, shown as cards. Each has an icon, a short title and a line of text.
const FACILITIES = [
  { icon: Armchair, title: 'Playing Area', text: 'Dedicated playing areas with chessboards and seating.' },
  { icon: Timer, title: 'Digital Clocks', text: 'FIDE-approved digital chess clocks for tournament practice.' },
  { icon: Monitor, title: 'Electronic Chessboard', text: 'For interactive learning and practice.' },
  { icon: BookOpen, title: 'Library', text: 'Chess books and educational resources.' },
  { icon: Scale, title: 'Arbiter Support', text: 'Support from experienced chess arbiters.' },
  {
    icon: Presentation,
    title: 'Lectures & Workshops',
    text: 'Opportunities to take part in special lectures, workshops and chess events.',
  },
]

export default function AboutPage() {
  return (
    <>
      <PageIntro eyebrow="About KICA" title="A Passion for Chess. A Community for Everyone.">
        Established in 2006, the Kuwait Indian Chess Association (KICA) has been bringing chess
        enthusiasts together for two decades, fostering a shared passion for the game and
        contributing to the development of chess in Kuwait.
      </PageIntro>

      <OurStory />
      <BigQuote />
      <Facilities />
      <JoinBand />
    </>
  )
}

/* ---------- Who we are, with the team photo ---------- */

function OurStory() {
  return (
    <section className="about-story">
      <div className="site-container about-story-inner">
        <Reveal className="about-story-text">
          <p>
            KICA is a non-commercial association run by dedicated volunteers, including
            experienced chess enthusiasts, professionals, and qualified chess arbiters who
            generously contribute their personal time to support the chess community.
          </p>
          <p>
            Rooted in its Indian chess community heritage, KICA welcomes chess enthusiasts of all
            nationalities, ages, and playing abilities. Our club celebrates diversity and believes
            that chess is a universal language that brings people together.
          </p>
          <p>
            Through weekly club gatherings, tournaments, interactive learning activities, and
            special events featuring internationally titled players, KICA encourages both
            recreational and competitive chess.
          </p>
          <p>
            With extensive experience in organising chess tournaments, including major
            competitions featuring more than 200 players, KICA has established itself as an active
            contributor to Kuwait&apos;s chess community.
          </p>
        </Reveal>

        <motion.div
          className="about-story-photo"
          initial={{ opacity: 0, x: 60 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, amount: 0.25 }}
          transition={{ duration: 0.8, ease: SMOOTH }}
        >
          <img src={teamPhoto} alt="The KICA team standing beside the club banner" loading="lazy" />
        </motion.div>
      </div>
    </section>
  )
}

/* ---------- The big quote ---------- */

function BigQuote() {
  return (
    <section className="about-quote">
      <div className="site-container">
        <Reveal className="about-quote-inner">
          <Quote size={40} aria-hidden="true" className="about-quote-icon" />
          <blockquote>
            We believe chess is more than a game. It develops critical thinking, concentration,
            discipline, sportsmanship, and lasting friendships, bringing people together through a
            shared passion.
          </blockquote>
        </Reveal>
      </div>
    </section>
  )
}

/* ---------- Our facilities, as cards ---------- */

function Facilities() {
  return (
    <section className="about-facilities">
      <div className="site-container">
        <Reveal className="section-heading">
          <p className="site-eyebrow">Our Facilities</p>
          <h2>A Welcoming Space to Play and Learn</h2>
          <p className="site-lead">
            KICA provides a comfortable environment and useful resources to support regular chess
            activities and competitive practice.
          </p>
          <p className="about-address">
            <MapPin size={20} aria-hidden="true" />
            <span>
              <strong>{CLUB.address}</strong>
              <span className="about-address-landmark">{CLUB.landmark}</span>
            </span>
          </p>
        </Reveal>

        <div className="feature-cards">
          {FACILITIES.map((facility, index) => (
            <Reveal key={facility.title} className="feature-card" delay={(index % 3) * 0.1}>
              <span className="feature-card-icon">
                <facility.icon size={24} aria-hidden="true" />
              </span>
              <h3>{facility.title}</h3>
              <p>{facility.text}</p>
            </Reveal>
          ))}
        </div>

        <Reveal className="about-facilities-note">
          <p className="site-lead">
            We strive to create an environment where players can enjoy the game, sharpen their
            skills, and interact with fellow chess enthusiasts.
          </p>
        </Reveal>
      </div>
    </section>
  )
}