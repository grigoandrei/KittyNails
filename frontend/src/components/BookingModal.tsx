import { useState, useEffect, useCallback } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { useForm } from "react-hook-form";
import { format, parseISO, addMonths, subMonths, isSameMonth, startOfMonth, getDay, getDaysInMonth, isSameDay } from "date-fns";
import { X, ChevronLeft, ChevronRight, Loader2, AlertCircle, Check, Clock, DollarSign } from "lucide-react";
import { toast } from "sonner";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import {
  fetchServices,
  fetchAvailableDates,
  fetchSlots,
  createAppointment,
  type Service,
} from "../api";

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

type Step = "service" | "datetime" | "info" | "review";

interface ClientInfo {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
}

interface BookingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function BookingModal({ open, onOpenChange }: BookingModalProps) {
  const [step, setStep] = useState<Step>("service");
  const [services, setServices] = useState<Service[]>([]);
  const [servicesLoading, setServicesLoading] = useState(false);
  const [selectedService, setSelectedService] = useState<Service | null>(null);

  // Date/time state
  const [calendarMonth, setCalendarMonth] = useState(startOfMonth(new Date()));
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [datesLoading, setDatesLoading] = useState(false);
  const [datesError, setDatesError] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [slotsError, setSlotsError] = useState<string | null>(null);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);

  // Submission
  const [submitting, setSubmitting] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    getValues,
    reset: resetForm,
  } = useForm<ClientInfo>({
    defaultValues: { firstName: "", lastName: "", email: "", phone: "" },
  });

  // Reset when modal opens/closes
  useEffect(() => {
    if (open) {
      setStep("service");
      setSelectedService(null);
      setSelectedDate(null);
      setSelectedTime(null);
      setCalendarMonth(startOfMonth(new Date()));
      setAvailableDates([]);
      setTimeSlots([]);
      setConfirmed(false);
      resetForm();
      loadServices();
    }
  }, [open, resetForm]);

  // Load services
  async function loadServices() {
    setServicesLoading(true);
    try {
      const data = await fetchServices();
      setServices(data);
    } catch {
      toast.error("Failed to load services. Please try again.");
    } finally {
      setServicesLoading(false);
    }
  }

  // Load available dates when service or month changes
  const loadAvailableDates = useCallback(async () => {
    if (!selectedService) return;
    setDatesLoading(true);
    setDatesError(null);
    try {
      const year = calendarMonth.getFullYear();
      const month = calendarMonth.getMonth() + 1;
      const dates = await fetchAvailableDates(selectedService.id, year, month);
      setAvailableDates(dates);
    } catch {
      setDatesError("Failed to load available dates.");
    } finally {
      setDatesLoading(false);
    }
  }, [selectedService, calendarMonth]);

  useEffect(() => {
    if (step === "datetime" && selectedService) {
      loadAvailableDates();
    }
  }, [step, selectedService, calendarMonth, loadAvailableDates]);

  // Load time slots when date is selected
  const loadTimeSlots = useCallback(async () => {
    if (!selectedService || !selectedDate) return;
    setSlotsLoading(true);
    setSlotsError(null);
    setSelectedTime(null);
    try {
      const dateStr = format(selectedDate, "yyyy-MM-dd");
      const slots = await fetchSlots(selectedService.id, dateStr);
      setTimeSlots(slots);
    } catch {
      setSlotsError("Failed to load time slots.");
    } finally {
      setSlotsLoading(false);
    }
  }, [selectedService, selectedDate]);

  useEffect(() => {
    if (selectedDate) {
      loadTimeSlots();
    }
  }, [selectedDate, loadTimeSlots]);

  // Navigation
  function goBack() {
    if (step === "datetime") setStep("service");
    else if (step === "info") setStep("datetime");
    else if (step === "review") setStep("info");
  }

  function selectService(service: Service) {
    setSelectedService(service);
    setSelectedDate(null);
    setSelectedTime(null);
    setTimeSlots([]);
    setStep("datetime");
  }

  function proceedToInfo() {
    if (!selectedTime) return;
    setStep("info");
  }

  function onInfoSubmit() {
    setStep("review");
  }

  async function confirmBooking() {
    if (!selectedService || !selectedTime) return;
    setSubmitting(true);
    try {
      const info = getValues();
      await createAppointment({
        service_id: selectedService.id,
        client_email: info.email,
        start_time: selectedTime,
      });
      setConfirmed(true);
      toast.success("Appointment booked successfully!");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to book appointment."
      );
    } finally {
      setSubmitting(false);
    }
  }

  // Calendar helpers
  const today = new Date();
  const canGoPrevMonth = !isSameMonth(calendarMonth, startOfMonth(today));

  function prevMonth() {
    if (canGoPrevMonth) {
      setCalendarMonth(subMonths(calendarMonth, 1));
      setSelectedDate(null);
      setTimeSlots([]);
    }
  }

  function nextMonth() {
    setCalendarMonth(addMonths(calendarMonth, 1));
    setSelectedDate(null);
    setTimeSlots([]);
  }

  function isDateAvailable(day: number): boolean {
    const dateStr = format(
      new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), day),
      "yyyy-MM-dd"
    );
    return availableDates.includes(dateStr);
  }

  function renderCalendar() {
    const daysInMonth = getDaysInMonth(calendarMonth);
    const firstDayOfWeek = getDay(startOfMonth(calendarMonth));
    const days: (number | null)[] = [];

    for (let i = 0; i < firstDayOfWeek; i++) {
      days.push(null);
    }
    for (let d = 1; d <= daysInMonth; d++) {
      days.push(d);
    }

    return (
      <div className="grid grid-cols-7 gap-1">
        {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((day) => (
          <div
            key={day}
            className="text-center text-xs text-muted-foreground font-medium py-2"
          >
            {day}
          </div>
        ))}
        {days.map((day, idx) => {
          if (day === null) {
            return <div key={`empty-${idx}`} />;
          }
          const available = isDateAvailable(day);
          const dateObj = new Date(
            calendarMonth.getFullYear(),
            calendarMonth.getMonth(),
            day
          );
          const isSelected = selectedDate && isSameDay(dateObj, selectedDate);

          return (
            <button
              key={day}
              disabled={!available}
              onClick={() => setSelectedDate(dateObj)}
              className={cn(
                "w-full aspect-square rounded-lg text-sm flex items-center justify-center transition-colors",
                available
                  ? "hover:bg-primary/10 cursor-pointer"
                  : "text-muted-foreground/40 cursor-not-allowed",
                isSelected && "bg-primary text-white hover:bg-primary-dark"
              )}
            >
              {day}
            </button>
          );
        })}
      </div>
    );
  }

  // Step indicator
  const steps: Step[] = ["service", "datetime", "info", "review"];
  const stepLabels = ["Service", "Date & Time", "Info", "Confirm"];
  const currentStepIndex = steps.indexOf(step);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[95vw] max-w-lg max-h-[90vh] overflow-y-auto bg-card rounded-2xl shadow-xl border border-border p-6">
          {/* Close button */}
          <Dialog.Close className="absolute top-4 right-4 p-1.5 text-muted-foreground hover:text-foreground rounded-lg hover:bg-secondary transition-colors">
            <X className="w-5 h-5" />
          </Dialog.Close>

          <Dialog.Title className="font-[family-name:var(--font-serif)] text-xl font-semibold mb-1">
            {confirmed ? "Booking Confirmed" : "Book an Appointment"}
          </Dialog.Title>
          <Dialog.Description className="text-sm text-muted-foreground mb-6">
            {confirmed
              ? "Your appointment has been scheduled."
              : stepLabels[currentStepIndex]}
          </Dialog.Description>

          {/* Step indicator */}
          {!confirmed && (
            <div className="flex items-center gap-1 mb-6">
              {steps.map((s, i) => (
                <div
                  key={s}
                  className={cn(
                    "h-1 flex-1 rounded-full transition-colors",
                    i <= currentStepIndex ? "bg-primary" : "bg-border"
                  )}
                />
              ))}
            </div>
          )}

          {/* Confirmed State */}
          {confirmed && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="w-8 h-8 text-success" />
              </div>
              <h3 className="font-semibold text-lg mb-2">You are all set!</h3>
              <p className="text-muted-foreground text-sm mb-4">
                A confirmation email will be sent to{" "}
                <span className="font-medium text-foreground">
                  {getValues().email}
                </span>
              </p>
              <div className="bg-secondary rounded-xl p-4 text-left text-sm space-y-1">
                <p>
                  <span className="text-muted-foreground">Service:</span>{" "}
                  {selectedService?.name}
                </p>
                <p>
                  <span className="text-muted-foreground">Date & Time:</span>{" "}
                  {selectedTime &&
                    format(
                      parseISO(selectedTime),
                      "MMM d, yyyy 'at' h:mm a"
                    )}
                </p>
              </div>
              <button
                onClick={() => onOpenChange(false)}
                className="mt-6 bg-primary text-primary-foreground px-6 py-2.5 rounded-full text-sm font-medium hover:bg-primary-dark transition-colors"
              >
                Done
              </button>
            </div>
          )}

          {/* Step 1: Service Selection */}
          {!confirmed && step === "service" && (
            <div>
              {servicesLoading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                  <span className="ml-2 text-sm text-muted-foreground">
                    Loading services...
                  </span>
                </div>
              )}
              {!servicesLoading && services.length === 0 && (
                <p className="text-center text-muted-foreground py-12">
                  No services available.
                </p>
              )}
              {!servicesLoading && services.length > 0 && (
                <div className="space-y-3">
                  {services.map((service) => (
                    <button
                      key={service.id}
                      onClick={() => selectService(service)}
                      className="w-full text-left p-4 rounded-xl border border-border hover:border-primary/50 hover:bg-primary/5 transition-colors"
                    >
                      <div className="font-medium">{service.name}</div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          {service.duration_minutes} min
                        </span>
                        <span className="flex items-center gap-1">
                          <DollarSign className="w-3.5 h-3.5" />
                          {service.price.toFixed(2)}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Step 2: Date & Time */}
          {!confirmed && step === "datetime" && (
            <div>
              {/* Calendar Header */}
              <div className="flex items-center justify-between mb-4">
                <button
                  onClick={prevMonth}
                  disabled={!canGoPrevMonth}
                  className={cn(
                    "p-1.5 rounded-lg transition-colors",
                    canGoPrevMonth
                      ? "hover:bg-secondary text-foreground"
                      : "text-muted-foreground/40 cursor-not-allowed"
                  )}
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm font-medium">
                  {format(calendarMonth, "MMMM yyyy")}
                </span>
                <button
                  onClick={nextMonth}
                  className="p-1.5 rounded-lg hover:bg-secondary text-foreground transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* Calendar */}
              {datesLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                  <span className="ml-2 text-sm text-muted-foreground">
                    Loading dates...
                  </span>
                </div>
              ) : datesError ? (
                <div className="text-center py-8">
                  <AlertCircle className="w-6 h-6 text-destructive mx-auto mb-2" />
                  <p className="text-sm text-destructive mb-3">{datesError}</p>
                  <button
                    onClick={loadAvailableDates}
                    className="text-sm text-primary hover:text-primary-dark underline underline-offset-4"
                  >
                    Retry
                  </button>
                </div>
              ) : (
                renderCalendar()
              )}

              {/* Time Slots */}
              {selectedDate && (
                <div className="mt-6 border-t border-border pt-4">
                  <h4 className="text-sm font-medium mb-3">
                    Available times for {format(selectedDate, "MMM d")}
                  </h4>

                  {slotsLoading && (
                    <div className="flex items-center justify-center py-6">
                      <Loader2 className="w-4 h-4 text-primary animate-spin" />
                      <span className="ml-2 text-sm text-muted-foreground">
                        Loading times...
                      </span>
                    </div>
                  )}

                  {slotsError && (
                    <div className="text-center py-4">
                      <p className="text-sm text-destructive mb-2">{slotsError}</p>
                      <button
                        onClick={loadTimeSlots}
                        className="text-sm text-primary hover:text-primary-dark underline underline-offset-4"
                      >
                        Retry
                      </button>
                    </div>
                  )}

                  {!slotsLoading && !slotsError && timeSlots.length === 0 && (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      No slots available for this date.
                    </p>
                  )}

                  {!slotsLoading && !slotsError && timeSlots.length > 0 && (
                    <div className="grid grid-cols-3 gap-2 max-h-40 overflow-y-auto">
                      {timeSlots.map((slot) => {
                        const time = parseISO(slot);
                        const isSelected = selectedTime === slot;
                        return (
                          <button
                            key={slot}
                            onClick={() => setSelectedTime(slot)}
                            className={cn(
                              "px-3 py-2 rounded-lg text-sm border transition-colors",
                              isSelected
                                ? "bg-primary text-white border-primary"
                                : "border-border hover:border-primary/50 hover:bg-primary/5"
                            )}
                          >
                            {format(time, "h:mm a")}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* Navigation */}
              <div className="flex justify-between mt-6 pt-4 border-t border-border">
                <button
                  onClick={goBack}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={proceedToInfo}
                  disabled={!selectedTime}
                  className={cn(
                    "px-5 py-2 rounded-full text-sm font-medium transition-colors",
                    selectedTime
                      ? "bg-primary text-primary-foreground hover:bg-primary-dark"
                      : "bg-border text-muted-foreground cursor-not-allowed"
                  )}
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Client Info */}
          {!confirmed && step === "info" && (
            <form onSubmit={handleSubmit(onInfoSubmit)} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium mb-1.5">
                    First Name
                  </label>
                  <input
                    {...register("firstName")}
                    placeholder="Jane"
                    className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5">
                    Last Name
                  </label>
                  <input
                    {...register("lastName")}
                    placeholder="Doe"
                    className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1.5">
                  Email <span className="text-destructive">*</span>
                </label>
                <input
                  {...register("email", {
                    required: "Email is required",
                    pattern: {
                      value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                      message: "Please enter a valid email",
                    },
                  })}
                  type="email"
                  placeholder="jane@example.com"
                  className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
                />
                {errors.email && (
                  <p className="text-xs text-destructive mt-1">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium mb-1.5">
                  Phone
                </label>
                <input
                  {...register("phone")}
                  type="tel"
                  placeholder="(555) 123-4567"
                  className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
                />
              </div>

              {/* Navigation */}
              <div className="flex justify-between pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={goBack}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="bg-primary text-primary-foreground px-5 py-2 rounded-full text-sm font-medium hover:bg-primary-dark transition-colors"
                >
                  Continue
                </button>
              </div>
            </form>
          )}

          {/* Step 4: Review & Confirm */}
          {!confirmed && step === "review" && (
            <div>
              <div className="bg-secondary rounded-xl p-4 space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Service</span>
                  <span className="font-medium">{selectedService?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Duration</span>
                  <span>{selectedService?.duration_minutes} min</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Price</span>
                  <span className="font-medium">
                    ${selectedService?.price.toFixed(2)}
                  </span>
                </div>
                <div className="border-t border-border my-2" />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Date & Time</span>
                  <span>
                    {selectedTime &&
                      format(
                        parseISO(selectedTime),
                        "MMM d, yyyy 'at' h:mm a"
                      )}
                  </span>
                </div>
                <div className="border-t border-border my-2" />
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Email</span>
                  <span>{getValues().email}</span>
                </div>
                {getValues().firstName && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Name</span>
                    <span>
                      {getValues().firstName} {getValues().lastName}
                    </span>
                  </div>
                )}
                {getValues().phone && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Phone</span>
                    <span>{getValues().phone}</span>
                  </div>
                )}
              </div>

              {/* Navigation */}
              <div className="flex justify-between mt-6 pt-4 border-t border-border">
                <button
                  onClick={goBack}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={confirmBooking}
                  disabled={submitting}
                  className={cn(
                    "px-5 py-2.5 rounded-full text-sm font-medium transition-colors flex items-center gap-2",
                    submitting
                      ? "bg-border text-muted-foreground cursor-not-allowed"
                      : "bg-primary text-primary-foreground hover:bg-primary-dark"
                  )}
                >
                  {submitting && (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  )}
                  {submitting ? "Booking..." : "Confirm Booking"}
                </button>
              </div>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
