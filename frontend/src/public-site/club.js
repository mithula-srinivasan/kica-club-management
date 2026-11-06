// The club's details, used across the public website. Change them here only.
export const CLUB = {
  name: 'Kuwait Indian Chess Association',
  shortName: 'KICA',
  tagline: 'Connecting Players, Developing Talent, Celebrating Chess',
  email: 'kica.chesskwt@gmail.com',
  instagram: 'kicachess',
  address: 'Building No. 1, Floor No. 1, Room No. 1, Block 1, Abu Halifa',
  landmark: 'Opposite Abu Halifa Park',
  // The club on Google Maps (used for the footer address, and the Home page's map button and QR code)
  mapsLink:
    'https://www.google.com/maps?q=KICA+Chess+Club+(+Kuwait+Indian+Chess+Assocation+),+Street+4&ftid=0x3fcf0919ce491377:0xf3ca6ef2fb935821',
  // \u00a0 is a space that never breaks, so "10 am" always stays on one line
    // \u00a0 is a space that never breaks, so "10:30 am" always stays on one line
  timings: [
    { label: 'Club Timings', time: 'Friday & Saturday, 10:30\u00a0am – 1:30\u00a0pm' },
  ],
}

export const INSTAGRAM_LINK = `https://www.instagram.com/${CLUB.instagram}/`