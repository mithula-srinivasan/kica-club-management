// The club's details, used across the public website. Change them here only.
export const CLUB = {
  name: 'Kuwait Indian Chess Association',
  shortName: 'KICA',
  tagline: 'Where Every Move Counts',
  email: 'kica.chesskwt@gmail.com',
  instagram: 'kicachess',
  // To do: the club's address and its Google Maps link
  location: 'Location coming soon',
  mapsLink: null,
  // \u00a0 is a space that never breaks, so "10 am" always stays on one line
  timings: [
    { label: 'Training', time: 'Friday & Saturday, 9–10\u00a0am' },
    { label: 'Club time', time: 'Friday & Saturday, 10\u00a0am – 2\u00a0pm' },
  ],
}

export const INSTAGRAM_LINK = `https://www.instagram.com/${CLUB.instagram}/`