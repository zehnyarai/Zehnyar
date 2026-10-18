// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it } from 'vitest'
import ScientificBasis from './ScientificBasis'
import { selectEvidence, buildScientificBasis } from '../evidence'
import reasoning from '../../tests/fixtures/decision-reasoning.json'

afterEach(cleanup)

it('shows differential reasoning and claim-specific transfer limits with registry-bound sources', async () => {
  const pack = selectEvidence({ notes: 'خشکیدگی تنه' })
  const basis = buildScientificBasis(
    {
      ...reasoning,
      research_claims: [
        {
          statement: 'جداسازی قارچ به‌تنهایی اثبات علت نیست.',
          source_ids: [pack[0].id],
          application_limit: 'این باغ در نمونه‌های کرمانشاه نبوده است.',
        },
      ],
    },
    pack
  )
  const { container } = render(<ScientificBasis basis={basis} />)
  await userEvent.click(screen.getByText(/منطق بررسی و پشتوانه/))
  expect(container.querySelector('details')!.open).toBe(true)
  for (const title of [
    'دلیل این برداشت از شواهد پرونده',
    'احتمال‌های جایگزین و شواهد مخالف',
    'چه بررسی‌ای تصمیم را تغییر می‌دهد؟',
    'اطلاعات ضروریِ مفقود',
    'معیار پیگیری و بازنگری',
    'چه زمانی به کارشناس ارجاع دهیم؟',
  ])
    expect(screen.getByRole('heading', { name: title })).toBeTruthy()
  expect(screen.getByText('این باغ در نمونه‌های کرمانشاه نبوده است.')).toBeTruthy()
  expect(screen.getByRole('link').getAttribute('href')).toBe(pack[0].url)
  expect(container.textContent).toContain('فقط چکیده ناشر')
  expect(container.textContent).toContain('تطابق معنایی')
  expect(container.textContent).not.toMatch(/gemini|grok|google|xai/i)
})
it('does not imply an old report was regenerated or checked against new science', () => {
  const { container } = render(<ScientificBasis />)
  expect(container.textContent).toContain('ثبت نشده')
  expect(container.querySelectorAll('a')).toHaveLength(0)
})
it('keeps no-citation evidence gaps explicit even when sources were supplied', () => {
  const basis = buildScientificBasis(reasoning, selectEvidence({ notes: 'پسیل' }))
  const { container } = render(<ScientificBasis basis={basis} />)
  expect(container.textContent).toContain('این خلأ شواهد است')
  expect(container.querySelectorAll('a')).toHaveLength(0)
})
it('never links to a forged source URL in imported local data', () => {
  const pack = selectEvidence({ notes: 'تنه' })
  const basis = buildScientificBasis(reasoning, pack)
  basis.sources = [{ ...pack[0], url: 'javascript:alert(1)' }]
  const { container } = render(<ScientificBasis basis={basis} />)
  expect(container.querySelectorAll('a')).toHaveLength(0)
})
