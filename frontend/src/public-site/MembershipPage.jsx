import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  ArrowRight,
  BadgeCheck,
  CalendarDays,
  ChessBishop,
  ChessKing,
  ChessKnight,
  ChessPawn,
  ChessQueen,
  ChessRook,
  FileText,
  MessageCircle,
  Wallet,
} from 'lucide-react'
import { CLUB } from './club'
import JoinBand from './JoinBand'
import PageIntro from './PageIntro'
import Reveal, { SMOOTH } from './Reveal'
import membershipPhoto from '../assets/photos/sections/membership.webp'

const REGISTER_LINK = '/join/register'

// What members get. Each one has a different chess piece as its "bullet".
const BENEFITS = [
  { icon: ChessPawn, text: 'Regular opportunities to play over-the-board chess' },
  { icon: ChessKnight, text: 'Friendly games, timed competitions, and club tournaments' },
  { icon: ChessBishop, text: 'Opportunities to develop tactical and strategic skills' },
  {
    icon: ChessRook,
    text: 'Access to chess workshops, educational activities, and learning resources',
  },
  {
    icon: ChessQueen,
    text: 'Interaction with experienced players, chess arbiters, and internationally titled professionals',
  },
  { icon: ChessKing, text: 'Connections and friendships with chess enthusiasts from diverse backgrounds' },
  { icon: ChessPawn, text: 'A welcoming environment for children, adults, and families' },
]

// How joining works, in order
const STEPS = [
  {
    icon: FileText,
    title: 'Register online',
    text: 'Fill in the new player form. It only takes a couple of minutes.',
    link: { label: 'Fill in the form', to: REGISTER_LINK },
  },
  {
    icon: MessageCircle,
    title: 'Request to join our WhatsApp group',
    text: 'Right after registering, you will see the link and QR code for the KICA Members WhatsApp group.',
  },
  {
    icon: BadgeCheck,
    title: 'Get approved',
    text: 'Once your registration is approved, you will be let into the group, where we share club timings, events, and updates.',
  },
]

export default function MembershipPage() {
  return (
    <>
      <PageIntro
        eyebrow="Membership"
        title="Join the KICA Family"
        actions={
          <Link to={REGISTER_LINK} className="site-button">
            Register a New Player
            <ArrowRight size={18} aria-hidden="true" />
          </Link>
        }
      >
        Chess brings people together, challenges the mind, and creates friendships that extend
        beyond the board.
      </PageIntro>

      <WhyJoin />
      <Benefits />
      <FeeAndTimings />
      <HowToJoin />

      <JoinBand
        title="Your Next Move Starts Here!"
        text="Whether you are a beginner, an aspiring tournament player, an experienced competitor, or someone who simply loves chess, there is a place for you at KICA."
        button="Register a New Player"
        to={REGISTER_LINK}
      />
    </>
  )
}

/* ---------- Why join: the award photo and a short introduction ---------- */

function WhyJoin() {
  return (
    <section className="page-split">
      <div className="site-container page-split-inner">
        <motion.div
          className="page-split-photo"
          initial={{ opacity: 0, x: -60 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, amount: 0.25 }}
          transition={{ duration: 0.8, ease: SMOOTH }}
        >
          <img
            src={membershipPhoto}
            alt="Young prize winners holding their trophies with the KICA team"
            loading="lazy"
          />
        </motion.div>

        <Reveal className="page-split-text">
          <p className="site-eyebrow">Why Join KICA?</p>
          <h2>More Than a Chess Club — A Community</h2>
          <p>
            At KICA, membership is about more than playing chess. It is about becoming part of a
            welcoming community that shares knowledge, encourages improvement, and celebrates the
            game together.
          </p>
        </Reveal>
      </div>
    </section>
  )
}

/* ---------- What members get: a checklist with chess-piece bullets ---------- */

function Benefits() {
  return (
    <section className="page-section">
      <div className="site-container">
        <Reveal className="section-heading">
          <p className="site-eyebrow">Being part of KICA offers</p>
          <h2>What Members Enjoy</h2>
        </Reveal>

        <ul className="benefits-list">
          {BENEFITS.map((benefit, index) => (
            <motion.li
              key={benefit.text}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.6 }}
              transition={{ duration: 0.5, delay: (index % 2) * 0.1, ease: SMOOTH }}
            >
              <span className="benefits-icon">
                <benefit.icon size={20} aria-hidden="true" />
              </span>
              {benefit.text}
            </motion.li>
          ))}
        </ul>

        <Reveal className="benefits-note">
          <p className="site-lead">
            Whether your goal is competitive improvement or simply enjoying chess with like-minded
            people, KICA offers a place where you belong.
          </p>
        </Reveal>
      </div>
    </section>
  )
}

/* ---------- The fee and the club timings, side by side ---------- */

function FeeAndTimings() {
  return (
    <section className="page-section">
      <div className="site-container info-cards">
        <Reveal className="info-card">
          <span className="feature-card-icon">
            <Wallet size={24} aria-hidden="true" />
          </span>
          <p className="site-eyebrow">Membership Fee</p>
          <p className="info-card-big">
            5 KWD <span>per month</span>
          </p>
        </Reveal>

        <Reveal className="info-card" delay={0.1}>
          <span className="feature-card-icon">
            <CalendarDays size={24} aria-hidden="true" />
          </span>
          <p className="site-eyebrow">Club Timings · Join Us Every Weekend</p>
          {CLUB.timings.map((timing) => (
            <p key={timing.label} className="info-card-big">
              {timing.time}
            </p>
          ))}
          <p className="info-card-text">
            Enjoy friendly games, timed chess, competitive practice, and interaction with fellow
            chess enthusiasts.
          </p>
        </Reveal>
      </div>
    </section>
  )
}

/* ---------- How to join: three steps ---------- */

function HowToJoin() {
  return (
    <section className="page-section">
      <div className="site-container">
        <Reveal className="section-heading">
          <p className="site-eyebrow">How to Join</p>
          <h2>Three Simple Steps</h2>
        </Reveal>

        <div className="join-steps">
          {STEPS.map((step, index) => (
            <Reveal key={step.title} className="join-step" delay={index * 0.12}>
              <div className="join-step-top">
                <span className="join-step-number">{index + 1}</span>
                <step.icon size={24} aria-hidden="true" className="join-step-icon" />
              </div>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
              {step.link && (
                <Link to={step.link.to} className="join-step-link">
                  {step.link.label}
                  <ArrowRight size={16} aria-hidden="true" />
                </Link>
              )}
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}