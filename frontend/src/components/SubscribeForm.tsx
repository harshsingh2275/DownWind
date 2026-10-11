import React, { useState, useId } from 'react'
import { Link } from '../router'
import { apiClient, ApiClientError } from '../api/client'
import type { City } from '../types/api'

export interface SubscribeFormProps {
  cities?: City[]
  defaultCityId?: string
  className?: string
  onSubscribed?: (cityId: string, email: string) => void
}

const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/

export function SubscribeForm({
  cities = [],
  defaultCityId,
  className = '',
  onSubscribed,
}: SubscribeFormProps) {
  const [selectedCityId, setSelectedCityId] = useState<string | null>(null)
  const [prevDefaultCityId, setPrevDefaultCityId] = useState<string | undefined>(defaultCityId)
  const [email, setEmail] = useState<string>('')
  const [emailTouched, setEmailTouched] = useState<boolean>(false)
  const [cityTouched, setCityTouched] = useState<boolean>(false)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const citySelectId = useId()
  const emailInputId = useId()
  const cityErrorId = useId()
  const emailErrorId = useId()
  const formHelpId = useId()

  let cityId = selectedCityId ?? defaultCityId ?? cities[0]?.id ?? ''
  if (defaultCityId !== prevDefaultCityId) {
    setPrevDefaultCityId(defaultCityId)
    setSelectedCityId(null)
    cityId = defaultCityId || cities[0]?.id || ''
  }

  const selectedCity = cities.find((c) => c.id === cityId)
  const cityName = selectedCity?.name || (cityId ? cityId.charAt(0).toUpperCase() + cityId.slice(1) : '')

  // Dynamic button label per task spec: "Subscribe to alerts for <city>"
  const buttonLabel = cityName
    ? `Subscribe to alerts for ${cityName}`
    : 'Subscribe to alerts'

  // Validation
  const isEmailValid = EMAIL_REGEX.test(email.trim())
  const emailError = emailTouched && !isEmailValid
    ? email.trim().length === 0
      ? 'Email address is required.'
      : 'Please enter a valid email address (e.g. name@example.com).'
    : null

  const cityError = cityTouched && !cityId
    ? 'Please select a monitored city.'
    : null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setEmailTouched(true)
    setCityTouched(true)
    setErrorMessage(null)

    if (!cityId) return
    if (!isEmailValid) return

    setIsSubmitting(true)
    try {
      const res = await apiClient.subscribe({
        email: email.trim().toLowerCase(),
        cityId,
      })

      setSuccessMessage(
        res.message || 'Check your inbox to confirm your subscription.'
      )
      onSubscribed?.(cityId, email.trim())
    } catch (err) {
      if (err instanceof ApiClientError) {
        setErrorMessage(err.message)
      } else if (err instanceof Error) {
        setErrorMessage(err.message)
      } else {
        setErrorMessage('Failed to submit subscription request. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleReset = () => {
    setSuccessMessage(null)
    setErrorMessage(null)
    setEmail('')
    setEmailTouched(false)
    setCityTouched(false)
    setSelectedCityId(null)
  }

  return (
    <div
      className={`border border-divider bg-surface p-5 space-y-4 ${className}`}
      role="region"
      aria-label="Smoke alert email subscription"
    >
      <div className="border-b border-divider pb-2">
        <h3 className="text-h3 font-semibold text-text m-0">
          Email Smoke Alerts
        </h3>
        <p id={formHelpId} className="text-small text-text-muted mt-1 mb-0">
          Get notified when wind models direct high-severity smoke trajectories toward your city.
        </p>
      </div>

      {/* Success State */}
      {successMessage ? (
        <div
          role="status"
          aria-live="polite"
          className="border border-divider bg-bg p-4 space-y-3"
        >
          <div className="flex items-start gap-2.5">
            <span
              className="w-3 h-3 bg-accent mt-1 inline-block shrink-0"
              aria-hidden="true"
            />
            <div className="space-y-1">
              <span className="font-semibold text-text text-body block">
                Subscription Request Sent
              </span>
              <p className="text-small text-text font-medium m-0">
                Check your inbox to confirm your subscription.
              </p>
              <p className="text-[12px] text-text-muted m-0 font-mono">
                AWS SNS has sent an automated verification link for <strong>{cityName}</strong> to <strong>{email}</strong>.
                Unconfirmed requests expire after 48 hours.
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-divider flex items-center justify-between">
            <button
              type="button"
              onClick={handleReset}
              className="text-accent hover:text-accent-hover underline text-small font-medium bg-transparent border-0 cursor-pointer p-0"
            >
              Subscribe another email
            </button>
            <span className="font-mono text-[11px] text-text-muted">
              Double opt-in verified
            </span>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {/* Error State with Retry Button */}
          {errorMessage && (
            <div
              role="alert"
              className="border border-accent bg-bg p-3 space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="text-small text-accent font-medium">
                  <strong>Subscription Error:</strong> {errorMessage}
                </div>
              </div>
              <div className="flex items-center gap-3 pt-1 border-t border-divider">
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="bg-accent hover:bg-accent-hover text-white text-[12px] font-medium px-3 py-1.5 border-0 cursor-pointer transition-colors"
                >
                  Retry subscription
                </button>
                <span className="text-[11px] text-text-muted font-mono">
                  You can retry or check your connection
                </span>
              </div>
            </div>
          )}

          {/* City Selection Input with Visible Label */}
          <div className="space-y-1.5">
            <label
              htmlFor={citySelectId}
              className="block font-medium text-text text-small"
            >
              Select Monitored City <span className="text-accent" aria-hidden="true">*</span>
            </label>

            <select
              id={citySelectId}
              value={cityId}
              onChange={(e) => {
                setSelectedCityId(e.target.value)
                setCityTouched(true)
              }}
              onBlur={() => setCityTouched(true)}
              aria-describedby={cityError ? cityErrorId : formHelpId}
              aria-invalid={cityError ? 'true' : undefined}
              className="w-full bg-bg text-text border border-divider px-3 py-2 text-small font-mono focus:border-focus focus:outline-none transition-colors cursor-pointer min-h-[44px]"
            >
              {cities.length === 0 ? (
                <option value="">Loading monitored cities...</option>
              ) : (
                cities.map((city) => (
                  <option key={city.id} value={city.id}>
                    {city.name} ({city.state})
                  </option>
                ))
              )}
            </select>

            {cityError && (
              <p
                id={cityErrorId}
                role="alert"
                className="text-accent text-[12px] font-mono m-0"
              >
                {cityError}
              </p>
            )}
          </div>

          {/* Email Input with Visible Label & aria-describedby Validation Error */}
          <div className="space-y-1.5">
            <label
              htmlFor={emailInputId}
              className="block font-medium text-text text-small"
            >
              Email Address <span className="text-accent" aria-hidden="true">*</span>
            </label>

            <input
              id={emailInputId}
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                if (emailTouched) setEmailTouched(true)
              }}
              onBlur={() => setEmailTouched(true)}
              placeholder="citizen@example.com"
              autoComplete="email"
              required
              aria-describedby={emailError ? emailErrorId : formHelpId}
              aria-invalid={emailError ? 'true' : undefined}
              className="w-full bg-bg text-text border border-divider px-3 py-2 text-small font-mono focus:border-focus focus:outline-none transition-colors min-h-[44px]"
            />

            {emailError && (
              <p
                id={emailErrorId}
                role="alert"
                className="text-accent text-[12px] font-mono m-0"
              >
                {emailError}
              </p>
            )}
          </div>

          {/* Submit Button with dynamic label and 0px radius */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-accent hover:bg-accent-hover text-white font-medium text-small min-h-[44px] px-4 py-2.5 border-0 cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <span>Submitting subscription request...</span>
            ) : (
              <span>{buttonLabel}</span>
            )}
          </button>

          {/* Privacy Link near the form per task spec */}
          <div className="pt-2 border-t border-divider flex flex-wrap items-center justify-between gap-2 text-[12px] text-text-muted">
            <div className="flex items-center gap-1.5">
              <span>Your email is strictly protected.</span>
              <Link
                href="/privacy"
                className="text-accent hover:text-accent-hover underline font-medium"
              >
                Privacy Policy
              </Link>
            </div>
            <span className="font-mono text-[11px]">
              12h cooldown • Zero spam
            </span>
          </div>
        </form>
      )}
    </div>
  )
}
