import { motion } from 'motion/react'
import { SMOOTH } from './Reveal'

// The title block at the top of each page:
// a small label, then the big heading on the left and a short intro on the right
// (both starting at the same height), then a faint line that leads into the page
export default function PageIntro({ eyebrow, title, children }) {
  return (
    <section className="page-intro">
      <motion.div
        className="site-container"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: SMOOTH }}
      >
        <p className="site-eyebrow page-intro-eyebrow">{eyebrow}</p>

        <div className="page-intro-inner">
          <h1>{title}</h1>
          {children && <p className="page-intro-lead">{children}</p>}
        </div>
      </motion.div>

      <div className="site-container">
        <motion.div
          className="page-intro-line"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 1.2, delay: 0.3, ease: SMOOTH }}
        />
      </div>
    </section>
  )
}