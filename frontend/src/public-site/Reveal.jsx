import { motion } from 'motion/react'

// A smooth "ease out" curve: starts quickly, then settles gently
export const SMOOTH = [0.22, 1, 0.36, 1]

// Wrap anything in <Reveal> and it fades and rises into place
// the first time it scrolls into view
export default function Reveal({ children, className, delay = 0 }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.25 }}
      transition={{ duration: 0.7, delay, ease: SMOOTH }}
    >
      {children}
    </motion.div>
  )
}