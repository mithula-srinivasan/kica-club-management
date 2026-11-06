import { motion } from 'motion/react'
import {
  Award,
  ChessKing,
  ChessKnight,
  ChessPawn,
  ClipboardList,
  Cpu,
  Crown,
  Lightbulb,
  Presentation,
  Puzzle,
  Scale,
  Search,
  Users,
} from 'lucide-react'
import { CLUB } from './club'
import JoinBand from './JoinBand'
import PageIntro from './PageIntro'
import Reveal, { SMOOTH } from './Reveal'
import matchPlayPhoto from '../assets/photos/belt/04-match-play.webp'
import tournamentHallPhoto from '../assets/photos/belt/01-tournament-hall.webp'
import trophiesPhoto from '../assets/photos/belt/03-trophies.webp'

const LEARNING = [
  { icon: Puzzle, title: 'Puzzles & Tactics', text: 'Interactive chess puzzles and tactical challenges.' },
  { icon: Lightbulb, title: 'Themed Sessions', text: 'Themed chess sessions and strategy discussions.' },
  { icon: Search, title: 'Game Analysis', text: 'Game analysis and knowledge-sharing sessions.' },
  { icon: Presentation, title: 'Lectures & Workshops', text: 'Conducted by experienced and titled players.' },
  {
    icon: Crown,
    title: 'Simultaneous Exhibitions',
    text: 'Play against Grandmasters and Woman International Masters.',
  },
  { icon: Users, title: 'Community Events', text: 'Community chess events and collaborative activities.' },
]

const SERVICES = [
  {
    icon: Scale,
    title: 'Qualified Chess Arbiters',
    text: 'Experienced, licensed, senior national arbiters, including FIDE-certified arbiters, to officiate and administer tournaments.',
  },
  {
    icon: Award,
    title: 'Rated Tournament Management',
    text: 'Technical expertise in conducting FIDE-rated and other officially recognised chess competitions, subject to applicable federation regulations and approvals.',
  },
  {
    icon: Users,
    title: 'Large-Scale Event Organisation',
    text: 'Experience managing tournaments of 200+ players, including player coordination, pairings, round management, results and standings.',
  },
  {
    icon: ClipboardList,
    title: 'Tournament Administration',
    text: 'Support with tournament formats, time controls, regulations, player registration, scheduling and overall event coordination.',
  },
  {
    icon: Cpu,
    title: 'Technical Expertise',
    text: 'Familiarity with tournament management systems, digital chess clocks and the administrative requirements of organised competitive chess.',
  },
]

const PARTNERS = [
  'Tamil Nadu Engineering Forum (TEF)',
  'Institute of Chartered Accountants of India (ICAI) – Kuwait Chapter',
  'The Indian Community School (TKS)',
  'KMSA (Kuwait Mind Sports Association)',
  'Chess House Academy',
  'Indians In Kuwait',
  'Al-Mulla',
  'Best Al-Yousifi',
]

// Opens an email to the club with the subject already filled in
const PARTNER_EMAIL = `mailto:${CLUB.email}?subject=${encodeURIComponent('Tournament partnership enquiry')}`

export default function ActivitiesPage() {
  return (
    <>
      <PageIntro eyebrow="Activities & Tournaments" title="More Than a Club: A Home for Competitive Chess">
        From friendly weekend games to major tournaments with hundreds of players, there&apos;s
        always something happening at KICA.
      </PageIntro>

      <PhotoSection
        photo={matchPlayPhoto}
        alt="Players in the middle of their games at a KICA club session"
        eyebrow="Weekly Chess Club Activities"
        title="Play. Practise. Connect."
        photoOnRight
      >
        <p>
          Our regular Friday and Saturday gatherings are at the heart of KICA&apos;s activities,
          offering members a welcoming space to enjoy over-the-board chess, improve their skills,
          and engage with fellow enthusiasts.
        </p>
        <p>
          From friendly games to competitive practice, our club sessions encourage players to
          challenge themselves, exchange ideas, and grow together.
        </p>
        <p>
          Regular activities include casual chess games, friendly competitions, timed games using
          digital chess clocks, and opportunities to analyse games and discuss strategies.
        </p>
      </PhotoSection>

      <PhotoSection
        photo={tournamentHallPhoto}
        alt="A full hall of players at a KICA tournament"
        eyebrow="Chess Tournaments & Competitions"
        title="From Club Competitions to Major Chess Tournaments"
      >
        <p>
          KICA has extensive experience in organising and conducting chess tournaments of various
          sizes, including large-scale competitions with more than 200 participants.
        </p>
        <p>
          Our activities include regular Friday tournaments, club-level competitions, and major
          annual chess events that attract players of different nationalities, ages, and skill
          levels. Selected tournaments are conducted with the approval or recognition of relevant
          chess federations, providing opportunities for players to take part in officially
          recognised competitions.
        </p>
        <p>
          KICA also collaborates with schools, organisations, chess federations, and community
          groups in organising chess tournaments and promoting competitive chess across Kuwait.
        </p>
      </PhotoSection>

      <CardsSection
        eyebrow="Learning, Workshops & Special Events"
        title="Discover. Learn. Improve."
        intro="KICA promotes continuous learning through engaging chess activities and special events designed to encourage players at every level."
        cards={LEARNING}
      />

      <Training />
      <TournamentServices />

      <JoinBand
        title="Planning a chess tournament for your institution or community?"
        text="Partner with KICA and let us help make it a successful event."
        button="Partner with KICA"
        href={PARTNER_EMAIL}
      />
    </>
  )
}

/* ---------- A section with a photo on one side and text on the other ---------- */

function PhotoSection({ photo, alt, eyebrow, title, photoOnRight = false, children }) {
  return (
    <section className={photoOnRight ? 'page-split photo-right' : 'page-split'}>
      <div className="site-container page-split-inner">
        <motion.div
          className="page-split-photo"
          initial={{ opacity: 0, x: photoOnRight ? 60 : -60 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, amount: 0.25 }}
          transition={{ duration: 0.8, ease: SMOOTH }}
        >
          <img src={photo} alt={alt} loading="lazy" />
        </motion.div>

        <Reveal className="page-split-text">
          <p className="site-eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
          {children}
        </Reveal>
      </div>
    </section>
  )
}

/* ---------- A heading, then a grid of icon cards ---------- */

function CardsSection({ eyebrow, title, intro, cards }) {
  return (
    <section className="page-section">
      <div className="site-container">
        <Reveal className="section-heading">
          <p className="site-eyebrow">{eyebrow}</p>
          <h2>{title}</h2>
          <p className="site-lead">{intro}</p>
        </Reveal>

        <div className="feature-cards">
          {cards.map((card, index) => (
            <Reveal key={card.title} className="feature-card" delay={(index % 3) * 0.1}>
              <span className="feature-card-icon">
                <card.icon size={24} aria-hidden="true" />
              </span>
              <h3>{card.title}</h3>
              <p>{card.text}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}



/* ---------- Chess training & coaching: the text, and "the chess journey" path ---------- */

// The three steps of the path. Each piece is "stronger" than the one before.
const JOURNEY = [
  { icon: ChessPawn, title: 'Beginner', text: 'Beginner-level instruction to build strong foundations.' },
  {
    icon: ChessKnight,
    title: 'Intermediate',
    text: 'Building skills, confidence and experience for competitive play.',
  },
  {
    icon: ChessKing,
    title: 'Advanced',
    text: 'Advanced coaching with internationally titled professionals.',
    titles: ['GM', 'IM', 'WIM'],
  },
]

function Training() {
  return (
    <section className="page-section">
      <div className="site-container training-inner">
        <Reveal className="page-text">
          <p className="site-eyebrow">Chess Training &amp; Coaching</p>
          <h2>Supporting Every Player&apos;s Chess Journey.</h2>
          <p>KICA recognises that players have different learning needs and aspirations.</p>
          <p>
            While KICA primarily operates as a community chess club rather than a commercial
            training academy, we help interested players connect with{' '}
            <strong>independent chess coaches and external training programmes</strong>, based on
            their experience and requirements.
          </p>
          <p>
            Training opportunities may range from beginner-level instruction to advanced coaching
            with internationally titled professionals, including Grandmasters (GM), International
            Masters (IM), and Woman International Masters (WIM).
          </p>
          <p>
            Our aim is to help players find suitable learning opportunities while continuing to
            promote chess as an enjoyable and rewarding activity.
          </p>
        </Reveal>

        <div className="journey">
          <ol className="journey-steps">
            {JOURNEY.map((step, index) => (
              <motion.li
                key={step.title}
                className="journey-step"
                initial={{ opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, amount: 0.6 }}
                transition={{ duration: 0.6, delay: 0.3 + index * 0.35, ease: SMOOTH }}
              >
                <span className="journey-icon">
                  <step.icon size={28} aria-hidden="true" />
                </span>

                {/* The maroon line down to the next step. It draws itself after this step appears. */}
                {index < JOURNEY.length - 1 && (
                  <motion.span
                    className="journey-line"
                    initial={{ scaleY: 0 }}
                    whileInView={{ scaleY: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.6 + index * 0.35, ease: SMOOTH }}
                  />
                )}

                <div className="journey-card">
                  <p className="journey-number">Step {index + 1}</p>
                  <h3>{step.title}</h3>
                  <p>{step.text}</p>
                  {step.titles && (
                    <div className="journey-titles">
                      {step.titles.map((title) => (
                        <span key={title}>{title}</span>
                      ))}
                    </div>
                  )}
                </div>
              </motion.li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  )
}

/* ---------- Tournament management & arbiter services ---------- */

function TournamentServices() {
  return (
    <>
      <PhotoSection
        photo={trophiesPhoto}
        alt="Trophies and medals ready for a KICA prize-giving"
        eyebrow="Tournament Management & Arbiter Services"
        title="Professional Expertise. Experienced Arbiters. Seamless Tournament Management."
        photoOnRight
      >
                <ul className="page-split-list">
          <li>
            KICA brings together a team of experienced senior chess arbiters, including FIDE
            (International Chess Federation)-certified arbiters, with the expertise and
            capabilities to organise and conduct professionally managed chess tournaments.
          </li>
          <li>
            With extensive hands-on experience in tournament organisation and administration, KICA
            supports institutions, community organisations, and corporate groups looking to host
            chess competitions for their members, students, employees, and wider communities.
          </li>
          <li>
            Over the past five years, KICA has successfully conducted and supported large-scale
            chess tournaments in Kuwait, including events with <strong>200+ participants</strong>,
            demonstrating its ability to manage competitive events involving significant numbers of
            players.
          </li>
        </ul>
      </PhotoSection>

      <section className="page-section page-section-tight" id="tournament-services">
        <div className="site-container">
          <Reveal className="section-heading">
            <h3 className="section-subheading">Our tournament management capabilities include:</h3>
          </Reveal>

          <div className="feature-cards">
            {SERVICES.map((service, index) => (
              <Reveal key={service.title} className="feature-card" delay={(index % 3) * 0.1}>
                <span className="feature-card-icon">
                  <service.icon size={24} aria-hidden="true" />
                </span>
                <h3>{service.title}</h3>
                <p>{service.text}</p>
              </Reveal>
            ))}
          </div>

          <Reveal className="partners">
            <p className="partners-label">We have supported chess events with</p>
            <ul className="partners-list">
              {PARTNERS.map((partner) => (
                <li key={partner}>{partner}</li>
              ))}
            </ul>
            <p className="partners-note">
              From community-level competitions to large-scale tournaments, KICA brings together
              the people, experience, and technical expertise needed to deliver well-organised
              chess events.
            </p>
          </Reveal>
        </div>
      </section>
    </>
  )
}