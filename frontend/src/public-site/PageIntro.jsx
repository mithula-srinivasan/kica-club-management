import { motion } from 'motion/react'
import { SMOOTH } from './Reveal'

// The title block at the top of each page: a small label, the big heading and a short intro
export default function PageIntro({ eyebrow, title, children }) {
  return (
    <section className="page-intro">
      <motion.div
        className="site-container page-intro-inner"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: SMOOTH }}
      >
        <p className="site-eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        {children && <p className="site-lead">{children}</p>}
      </motion.div>
    </section>
  )
}

