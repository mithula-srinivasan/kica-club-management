import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation, useOutlet } from 'react-router-dom'
import { AnimatePresence, MotionConfig, motion } from 'motion/react'
import { Clock, LogIn, Mail, MapPin, Menu, X } from 'lucide-react'
import { CLUB, INSTAGRAM_LINK } from './club'
import './public-site.css'

// The pages in the top menu, in order
const PAGES = [
  { to: '/', label: 'Home', end: true },
  { to: '/about', label: 'About KICA' },
  { to: '/activities', label: 'Activities & Tournaments' },
  { to: '/membership', label: 'Membership' },
]

export default function PublicLayout() {
  const location = useLocation()
  const outlet = useOutlet()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  // Once the page is scrolled a little, the top bar turns see-through with a blur
  useEffect(() => {
    function checkScroll() {
      setScrolled(window.scrollY > 12)
    }

    checkScroll()
    window.addEventListener('scroll', checkScroll, { passive: true })

    return () => window.removeEventListener('scroll', checkScroll)
  }, [])

  // While the phone menu is open: stop the page behind it scrolling, and let Esc close it
  useEffect(() => {
    if (!menuOpen) {
      return
    }

    function closeOnEscape(event) {
      if (event.key === 'Escape') setMenuOpen(false)
    }

    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', closeOnEscape)

    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', closeOnEscape)
    }
  }, [menuOpen])

  function closeMenu() {
    setMenuOpen(false)
  }

  return (
    // reducedMotion="user": people whose phone is set to "reduce motion" get calm, simple fades
    <MotionConfig reducedMotion="user">
      <div className="site">
        <header className={scrolled ? 'site-header scrolled' : 'site-header'}>
          <div className="site-container site-header-inner">
            <Link to="/" className="site-brand">
              <img src="/kica-logo.png" alt="" className="site-brand-logo" />
              <span className="site-brand-text">
                <strong>{CLUB.shortName}</strong>
              </span>
            </Link>

            <nav className="site-nav" aria-label="Main">
              {PAGES.map((page) => (
                <NavLink key={page.to} to={page.to} end={page.end} className="site-nav-link">
                  {({ isActive }) => (
                    <>
                      {page.label}
                      {isActive && (
                        <motion.span
                          layoutId="site-nav-underline"
                          className="site-nav-underline"
                          transition={{ type: 'spring', stiffness: 500, damping: 40 }}
                        />
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>

            <Link to="/exec/login" className="site-login">
              <LogIn size={18} aria-hidden="true" />
              Exec login
            </Link>

            <button
              type="button"
              className="site-menu-button"
              onClick={() => setMenuOpen(true)}
              aria-label="Open menu"
              aria-expanded={menuOpen}
            >
              <Menu size={26} aria-hidden="true" />
            </button>
          </div>
        </header>

        {/* Phones: a full-screen menu that fades in, with the links sliding up one by one */}
        <AnimatePresence>
          {menuOpen && (
            <motion.div
              className="site-mobile-menu"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <button
                type="button"
                className="site-menu-button site-menu-close"
                onClick={closeMenu}
                aria-label="Close menu"
              >
                <X size={28} aria-hidden="true" />
              </button>

              <nav aria-label="Main">
                {PAGES.map((page, index) => (
                  <motion.div
                    key={page.to}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.06 * index + 0.05, duration: 0.3 }}
                  >
                    <NavLink to={page.to} end={page.end} onClick={closeMenu}>
                      {page.label}
                    </NavLink>
                  </motion.div>
                ))}

                <Link to="/exec/login" className="site-login" onClick={closeMenu}>
                  <LogIn size={18} aria-hidden="true" />
                  Exec login
                </Link>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Moving between pages: the old page fades out, the new one fades and slides in */}
        <main className="site-main">
          <AnimatePresence mode="wait" onExitComplete={() => window.scrollTo({ top: 0 })}>
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            >
              {outlet}
            </motion.div>
          </AnimatePresence>
        </main>

        <SiteFooter />
      </div>
    </MotionConfig>
  )
}




function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-container site-footer-grid">
        <div className="site-footer-brand">
          <p className="site-footer-name">{CLUB.tagline}</p>
          <p className="site-footer-small">
            © {new Date().getFullYear()} {CLUB.name}
          </p>
        </div>

        <div>
          <h2 className="site-footer-title">Visit us</h2>
          <ul className="site-footer-list">
            {CLUB.timings.map((timing) => (
              <li key={timing.label}>
                <Clock size={18} aria-hidden="true" />
                <span>
                  <strong>{timing.label}:</strong> {timing.time}
                </span>
              </li>
            ))}
          <li>
              <MapPin size={18} aria-hidden="true" />
              <span>
                  <strong className="site-footer-address">
                  {CLUB.mapsLink ? (
                    <a href={CLUB.mapsLink} target="_blank" rel="noopener noreferrer">
                      {CLUB.address}
                    </a>
                  ) : (
                    CLUB.address
                  )}
                </strong>
                <span className="site-footer-landmark">{CLUB.landmark}</span>
              </span>
            </li>
          </ul>
        </div>

        <div>
          <h2 className="site-footer-title">Contact</h2>
          <ul className="site-footer-list">
            <li>
              <Mail size={18} aria-hidden="true" />
              <a href={`mailto:${CLUB.email}`}>{CLUB.email}</a>
            </li>
            <li>
              <InstagramIcon />
              <a href={INSTAGRAM_LINK} target="_blank" rel="noopener noreferrer">
                @{CLUB.instagram}
              </a>
            </li>
          </ul>
          
        </div>
      </div>
    </footer>
  )
}

// Lucide doesn't include brand logos, so this is a simple Instagram-style icon
function InstagramIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none" />
    </svg>
  )
}