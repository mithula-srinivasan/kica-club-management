// The club's details, used across the public website. Change them here only.
export const CLUB = {
  name: 'Kuwait Indian Chess Association',
  shortName: 'KICA',
  tagline: 'Connecting Players, Developing Talent, Celebrating Chess',
  email: 'kica.chesskwt@gmail.com',
  instagram: 'kicachess',
  address: 'Building No. 1, Floor No. 1, Room No. 1, Block 1, Abu Halifa',
  landmark: 'Opposite Abu Halifa Park',
  // To do: the club's Google Maps link (Google Maps → the club → Share → Copy link)
  mapsLink: null,
  // \u00a0 is a space that never breaks, so "10 am" always stays on one line
  timings: [
    { label: 'Training', time: 'Friday & Saturday, 9–10\u00a0am' },
    { label: 'Club time', time: 'Friday & Saturday, 10\u00a0am – 2\u00a0pm' },
  ],
}

export const INSTAGRAM_LINK = `https://www.instagram.com/${CLUB.instagram}/`