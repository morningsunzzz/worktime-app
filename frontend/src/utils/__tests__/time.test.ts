import { describe, it, expect } from 'vitest'
import {
  roundToHalfHour,
  calcWorkMinutes,
  calcTotalHours,
  calcOvertimeHours,
  formatTime,
  formatHours,
  formatMinutesToHM,
} from '../time'

// ═══════════════════════════════════════════════════════════════════
// roundToHalfHour — 工时精确到 0.5h 取整
// ═══════════════════════════════════════════════════════════════════

describe('roundToHalfHour', () => {
  it('exact hour: 0min → 0.0h, 60min → 1.0h, 480min → 8.0h', () => {
    expect(roundToHalfHour(0)).toBe(0.0)
    expect(roundToHalfHour(60)).toBe(1.0)
    expect(roundToHalfHour(120)).toBe(2.0)
    expect(roundToHalfHour(480)).toBe(8.0)
  })

  it('exact half hour: 30min → 0.5h, 510min → 8.5h', () => {
    expect(roundToHalfHour(30)).toBe(0.5)
    expect(roundToHalfHour(90)).toBe(1.5)
    expect(roundToHalfHour(510)).toBe(8.5)
  })

  it('rounds up: 16min → 0.5h, 46min → 1.0h', () => {
    expect(roundToHalfHour(16)).toBe(0.5)
    expect(roundToHalfHour(29)).toBe(0.5)
    expect(roundToHalfHour(46)).toBe(1.0)
    expect(roundToHalfHour(59)).toBe(1.0)
  })

  it('rounds down: 1min → 0.0h, 44min → 0.5h', () => {
    expect(roundToHalfHour(1)).toBe(0.0)
    expect(roundToHalfHour(14)).toBe(0.0)
    expect(roundToHalfHour(44)).toBe(0.5)
  })

  it('boundary: 15min → 0.5h, 45min → 1.0h', () => {
    // JS Math.round(0.5) = 1, not banker's rounding
    expect(roundToHalfHour(15)).toBe(0.5)
    expect(roundToHalfHour(45)).toBe(1.0)
  })
})

// ═══════════════════════════════════════════════════════════════════
// calcWorkMinutes — (下班-上班) - 午休，最少 0
// ═══════════════════════════════════════════════════════════════════

describe('calcWorkMinutes', () => {
  it('standard 9:00-18:00 with 1h lunch = 480min', () => {
    expect(calcWorkMinutes('2026-05-26T09:00:00', '2026-05-26T18:00:00', 60)).toBe(480)
  })

  it('no lunch break = 540min', () => {
    expect(calcWorkMinutes('2026-05-26T09:00:00', '2026-05-26T18:00:00', 0)).toBe(540)
  })

  it('overtime to 22:00 = 720min', () => {
    expect(calcWorkMinutes('2026-05-26T09:00:00', '2026-05-26T22:00:00', 60)).toBe(720)
  })

  it('half day: 9:00-12:00 with 1h lunch = 120min', () => {
    expect(calcWorkMinutes('2026-05-26T09:00:00', '2026-05-26T12:00:00', 60)).toBe(120)
  })

  it('cross midnight: 36h = 2100min with 1h lunch', () => {
    const result = calcWorkMinutes('2026-05-26T09:00:00', '2026-05-27T21:00:00', 60)
    expect(result).toBe(2100)
  })

  it('lunch longer than work → 0', () => {
    expect(calcWorkMinutes('2026-05-26T09:00:00', '2026-05-26T09:30:00', 60)).toBe(0)
  })

  it('equal clock in/out → 0', () => {
    expect(calcWorkMinutes('2026-05-26T09:00:00', '2026-05-26T09:00:00', 0)).toBe(0)
  })

  it('one minute work → 1min', () => {
    expect(calcWorkMinutes('2026-05-26T09:00:00', '2026-05-26T09:01:00', 0)).toBe(1)
  })
})

// ═══════════════════════════════════════════════════════════════════
// calcTotalHours — roundToHalfHour(workMinutes)
// ═══════════════════════════════════════════════════════════════════

describe('calcTotalHours', () => {
  it('480min → 8.0h', () => {
    expect(calcTotalHours(480)).toBe(8.0)
  })

  it('510min → 8.5h', () => {
    expect(calcTotalHours(510)).toBe(8.5)
  })

  it('0min → 0.0h', () => {
    expect(calcTotalHours(0)).toBe(0.0)
  })
})

// ═══════════════════════════════════════════════════════════════════
// calcOvertimeHours — 早班加成 + 晚间加班（overtime_start之后）
// ═══════════════════════════════════════════════════════════════════

describe('calcOvertimeHours', () => {
  it('no clockOut → 0 overtime', () => {
    expect(calcOvertimeHours('2026-05-26T09:00:00', null, 1, '18:00')).toBe(0)
  })

  it('standard day no overtime: 9:00-18:00, ot_start=18:00', () => {
    expect(calcOvertimeHours('2026-05-26T09:00:00', '2026-05-26T18:00:00', 1, '18:00')).toBe(0)
  })

  it('morning bonus only: 8:00-17:00, ot_start=18:00 → 1h', () => {
    expect(calcOvertimeHours('2026-05-26T08:00:00', '2026-05-26T17:00:00', 1, '18:00')).toBe(1)
  })

  it('evening overtime only: 9:00-20:00, ot_start=18:00 → 2h', () => {
    expect(calcOvertimeHours('2026-05-26T09:00:00', '2026-05-26T20:00:00', 1, '18:00')).toBe(2)
  })

  it('morning + evening: 8:00-22:00, ot_start=18:00 → 5h', () => {
    expect(calcOvertimeHours('2026-05-26T08:00:00', '2026-05-26T22:00:00', 1, '18:00')).toBe(5)
  })

  it('change overtime_start to 19:00 → 9:00-20:00 = 1h', () => {
    expect(calcOvertimeHours('2026-05-26T09:00:00', '2026-05-26T20:00:00', 1, '19:00')).toBe(1)
  })

  it('change overtime_start to 18:30 → 9:00-19:00 = 0.5h', () => {
    expect(calcOvertimeHours('2026-05-26T09:00:00', '2026-05-26T19:00:00', 1, '18:30')).toBe(0.5)
  })

  it('exactly 9:00 → no morning bonus', () => {
    expect(calcOvertimeHours('2026-05-26T09:00:00', '2026-05-26T22:00:00', 1, '18:00')).toBe(4)
  })

  it('8:59 → gets morning bonus', () => {
    expect(calcOvertimeHours('2026-05-26T08:59:00', '2026-05-26T22:00:00', 1, '18:00')).toBe(5)
  })

  it('pre_hours=0 → no morning bonus', () => {
    expect(calcOvertimeHours('2026-05-26T08:00:00', '2026-05-26T20:00:00', 0, '18:00')).toBe(2)
  })

  it('cross-midnight: ot_start anchored to clock_in date', () => {
    expect(calcOvertimeHours(
      '2026-05-26T09:00:00',
      '2026-05-27T02:00:00',
      1,
      '18:00'
    )).toBe(8)
  })
})

// ═══════════════════════════════════════════════════════════════════
// formatTime — ISO → HH:mm
// ═══════════════════════════════════════════════════════════════════

describe('formatTime', () => {
  it('formats valid ISO', () => {
    expect(formatTime('2026-05-26T09:05:00')).toBe('09:05')
    expect(formatTime('2026-05-26T18:30:00')).toBe('18:30')
  })

  it('null returns placeholder', () => {
    expect(formatTime(null)).toBe('--:--')
  })

  it('midnight', () => {
    expect(formatTime('2026-05-26T00:00:00')).toBe('00:00')
  })
})

// ═══════════════════════════════════════════════════════════════════
// formatHours — number → "Xh" or "--" for null/NaN
// ═══════════════════════════════════════════════════════════════════

describe('formatHours', () => {
  it('formats valid numbers', () => {
    expect(formatHours(8)).toBe('8h')
    expect(formatHours(8.5)).toBe('8.5h')
    expect(formatHours(0)).toBe('0h')
  })

  it('null → placeholder', () => {
    expect(formatHours(null)).toBe('--')
  })

  it('NaN → placeholder', () => {
    expect(formatHours(NaN)).toBe('--')
  })
})

// ═══════════════════════════════════════════════════════════════════
// formatMinutesToHM — minutes → "Xh Ym"
// ═══════════════════════════════════════════════════════════════════

describe('formatMinutesToHM', () => {
  it('0min', () => {
    expect(formatMinutesToHM(0)).toBe('0h 0m')
  })

  it('exact hours', () => {
    expect(formatMinutesToHM(60)).toBe('1h 0m')
    expect(formatMinutesToHM(480)).toBe('8h 0m')
  })

  it('hours and minutes', () => {
    expect(formatMinutesToHM(510)).toBe('8h 30m')
    expect(formatMinutesToHM(75)).toBe('1h 15m')
  })

  it('minutes only', () => {
    expect(formatMinutesToHM(5)).toBe('0h 5m')
    expect(formatMinutesToHM(59)).toBe('0h 59m')
  })

  it('large values', () => {
    expect(formatMinutesToHM(1380)).toBe('23h 0m')
  })
})
