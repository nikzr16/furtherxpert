// Domain constants mirrored from the backend (never re-derive scores in the
// client -- proj-furtherxpert-rules skill: "the client only displays
// results"). These are fixed, stable lists, not computed values, so mirroring
// them here is just UI plumbing (dropdown options), not duplicated business
// logic.

// backend/app/models/spm_result.py SPM_GRADES -- no B-, C-, or F in SPM.
export const SPM_GRADES = ['A+', 'A', 'A-', 'B+', 'B', 'C+', 'C', 'D', 'E', 'G']

// backend/app/services/results.py REQUIRED_SUBJECT_CODES -- syarat am always
// needs Bahasa Melayu and Sejarah, so every SPM results save must include both.
export const REQUIRED_SUBJECT_CODES = ['BM', 'SJ']

// backend/app/models/user.py RACES -- PRD T4: race is collected only to check
// Bumiputera-only programs.
export const RACES = [
  'Melayu',
  'Cina',
  'India',
  'Anak Negeri Sabah',
  'Anak Negeri Sarawak',
  'Orang Asli',
  'Lain-lain',
]

// backend/app/importer/subjects.py SUBJECT_GROUPS -- all 7 groups, in the
// same order GET /me/analysis uses (by code). The "excel" chart shows every
// group; one the student took no subjects in shows "N/A" (decision 0019).
export const SUBJECT_GROUPS = [
  { code: 'ARTS', name: 'Arts' },
  { code: 'COMMERCE', name: 'Commerce' },
  { code: 'HUMANITIES', name: 'Humanities' },
  { code: 'LANGUAGES', name: 'Languages' },
  { code: 'MATHEMATICS', name: 'Mathematics' },
  { code: 'SCIENCES', name: 'Sciences' },
  { code: 'TECHNICAL_ICT', name: 'Technical & ICT' },
]

export const MIN_PASSWORD_LENGTH = 8
