import { useState, useEffect, useCallback } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { useForm } from "react-hook-form";
import { format, parseISO, addMonths, subMonths, isSameMonth, startOfMonth, getDay, getDaysInMonth, isSameDay } from "date-fns";
import { X, ChevronLeft, ChevronRight, Loader2, AlertCircle, Check, Clock, Upload, Sparkles, Info, Leaf } from "lucide-react";
import { toast } from "sonner";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import {
  analyzeNails,
  fetchAvailableDates,
  fetchSlots,
  fetchNailTypes,
  createAppointment,
  type NailAnalysisResponse,
  type NailType,
} from "../api";

function cn(...inputs: (string | undefined | null | false)[]) {
  return twMerge(clsx(inputs));
}

type Step = "photo" | "estimate" | "datetime" | "confirm";

interface ClientInfo {
  email: string;
  phone: string;
}

interface BookingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function BookingModal({ open, onOpenChange }: BookingModalProps) {
  const [step, setStep] = useState<Step>("photo");

  // Photo upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  // AI estimate
  const [analysis, setAnalysis] = useState<NailAnalysisResponse | null>(null);

  // Japanese Manicure flow (skips AI)
  const [japaneseManicure, setJapaneseManicure] = useState<NailType | null>(null);

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
    defaultValues: { email: "", phone: "" },
  });

  // Reset when modal opens/closes
  useEffect(() => {
    if (open) {
      setStep("photo");
      setSelectedFile(null);
      setPreviewUrl(null);
      setAnalyzing(false);
      setAnalyzeError(null);
      setAnalysis(null);
      setJapaneseManicure(null);
      setSelectedDate(null);
      setSelectedTime(null);
      setCalendarMonth(startOfMonth(new Date()));
      setAvailableDates([]);
      setTimeSlots([]);
      setConfirmed(false);
      resetForm();
    }
  }, [open, resetForm]);

  // Clean up preview URL
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  // Photo handling
  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Please select an image file");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error("Image must be under 5 MB");
      return;
    }

    setSelectedFile(file);
    setAnalyzeError(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(file));
  }

  async function handleAnalyze() {
    if (!selectedFile) return;
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const result = await analyzeNails(selectedFile);
      setAnalysis(result);
      setStep("estimate");
    } catch (err) {
      setAnalyzeError(
        err instanceof Error ? err.message : "Analysis failed. Please try again."
      );
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleJapaneseManicure() {
    try {
      const nailTypes = await fetchNailTypes();
      const jp = nailTypes.find((nt) => nt.name === "Japanese Manicure");
      if (!jp) {
        toast.error("Japanese Manicure is not currently available.");
        return;
      }
      setJapaneseManicure(jp);
      setAnalysis(null);
      setStep("datetime");
    } catch {
      toast.error("Failed to load service. Please try again.");
    }
  }

  // Load available dates when entering datetime step or month changes
  const loadAvailableDates = useCallback(async () => {
    const nailTypeId = analysis?.nail_type_id ?? japaneseManicure?.id;
    if (!nailTypeId) return;
    setDatesLoading(true);
    setDatesError(null);
    try {
      const year = calendarMonth.getFullYear();
      const month = calendarMonth.getMonth() + 1;
      const designTierId = analysis?.design_tier_id ?? null;
      const dates = await fetchAvailableDates(
        nailTypeId,
        designTierId,
        year,
        month
      );
      setAvailableDates(dates);
    } catch {
      setDatesError("Failed to load available dates.");
    } finally {
      setDatesLoading(false);
    }
  }, [analysis, japaneseManicure, calendarMonth]);

  useEffect(() => {
    if (step === "datetime" && (analysis || japaneseManicure)) {
      loadAvailableDates();
    }
  }, [step, analysis, japaneseManicure, calendarMonth, loadAvailableDates]);

  // Load time slots when date is selected
  const loadTimeSlots = useCallback(async () => {
    const nailTypeId = analysis?.nail_type_id ?? japaneseManicure?.id;
    if (!nailTypeId || !selectedDate) return;
    setSlotsLoading(true);
    setSlotsError(null);
    setSelectedTime(null);
    try {
      const dateStr = format(selectedDate, "yyyy-MM-dd");
      const designTierId = analysis?.design_tier_id ?? null;
      const slots = await fetchSlots(
        nailTypeId,
        designTierId,
        dateStr
      );
      setTimeSlots(slots);
    } catch {
      setSlotsError("Failed to load time slots.");
    } finally {
      setSlotsLoading(false);
    }
  }, [analysis, japaneseManicure, selectedDate]);

  useEffect(() => {
    if (selectedDate) {
      loadTimeSlots();
    }
  }, [selectedDate, loadTimeSlots]);

  // Navigation
  function goBack() {
    if (step === "estimate") setStep("photo");
    else if (step === "datetime") {
      if (japaneseManicure) setStep("photo");
      else setStep("estimate");
    }
    else if (step === "confirm") setStep("datetime");
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

  async function confirmBooking() {
    if (!selectedTime) return;
    const nailTypeId = analysis?.nail_type_id ?? japaneseManicure?.id;
    if (!nailTypeId) return;
    setSubmitting(true);
    try {
      const info = getValues();
      await createAppointment({
        nail_type_id: nailTypeId,
        design_tier_id: analysis?.design_tier_id ?? null,
        client_email: info.email,
        start_time: selectedTime,
        ai_confidence: analysis?.confidence,
        ai_reasoning: analysis?.reasoning,
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

  // Step indicator
  const steps: Step[] = ["photo", "estimate", "datetime", "confirm"];
  const stepLabels = ["Upload Photo", "Estimate", "Date & Time", "Confirm"];
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
              {steps.map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "h-1 flex-1 rounded-full transition-colors",
                    i <= currentStepIndex ? "bg-primary" : "bg-border"
                  )}
                />
              ))}
            </div>
          )}

          {/* Confirmed State */}
          {confirmed && <ConfirmedView analysis={analysis} japaneseManicure={japaneseManicure} selectedTime={selectedTime} email={getValues().email} onClose={() => onOpenChange(false)} />}

          {/* Step 1: Photo Upload */}
          {!confirmed && step === "photo" && (
            <PhotoStep
              previewUrl={previewUrl}
              selectedFile={selectedFile}
              analyzing={analyzing}
              analyzeError={analyzeError}
              onFileSelect={handleFileSelect}
              onAnalyze={handleAnalyze}
              onJapaneseManicure={handleJapaneseManicure}
            />
          )}

          {/* Step 2: AI Estimate */}
          {!confirmed && step === "estimate" && (
            <EstimateStep analysis={analysis} onContinue={() => setStep("datetime")} onBack={goBack} />
          )}

          {/* Step 3: Date & Time */}
          {!confirmed && step === "datetime" && (
            <DateTimeStep
              calendarMonth={calendarMonth}
              canGoPrevMonth={canGoPrevMonth}
              datesLoading={datesLoading}
              datesError={datesError}
              selectedDate={selectedDate}
              timeSlots={timeSlots}
              slotsLoading={slotsLoading}
              slotsError={slotsError}
              selectedTime={selectedTime}
              onPrevMonth={prevMonth}
              onNextMonth={nextMonth}
              onSelectTime={setSelectedTime}
              onRetryDates={loadAvailableDates}
              onRetrySlots={loadTimeSlots}
              onContinue={() => setStep("confirm")}
              onBack={goBack}
              renderCalendar={() => renderCalendar(calendarMonth, selectedDate, isDateAvailable, setSelectedDate)}
            />
          )}

          {/* Step 4: Confirm */}
          {!confirmed && step === "confirm" && (
            <ConfirmStep
              analysis={analysis}
              japaneseManicure={japaneseManicure}
              selectedTime={selectedTime}
              submitting={submitting}
              register={register}
              errors={errors}
              onSubmit={handleSubmit(confirmBooking)}
              onBack={goBack}
            />
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

// --- Sub-components ---

function renderCalendar(
  calendarMonth: Date,
  selectedDate: Date | null,
  isDateAvailable: (day: number) => boolean,
  setSelectedDate: (d: Date) => void
) {
  const daysInMonth = getDaysInMonth(calendarMonth);
  const firstDayOfWeek = getDay(startOfMonth(calendarMonth));
  const days: (number | null)[] = [];

  for (let i = 0; i < firstDayOfWeek; i++) days.push(null);
  for (let d = 1; d <= daysInMonth; d++) days.push(d);

  return (
    <div className="grid grid-cols-7 gap-1">
      {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((day) => (
        <div key={day} className="text-center text-xs text-muted-foreground font-medium py-2">
          {day}
        </div>
      ))}
      {days.map((day, idx) => {
        if (day === null) return <div key={`empty-${idx}`} />;
        const available = isDateAvailable(day);
        const dateObj = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), day);
        const isSelected = selectedDate && isSameDay(dateObj, selectedDate);

        return (
          <button
            key={day}
            disabled={!available}
            onClick={() => setSelectedDate(dateObj)}
            className={cn(
              "w-full aspect-square rounded-lg text-sm flex items-center justify-center transition-colors",
              available ? "hover:bg-primary/10 cursor-pointer" : "text-muted-foreground/40 cursor-not-allowed",
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

function ConfirmedView({ analysis, japaneseManicure, selectedTime, email, onClose }: {
  analysis: NailAnalysisResponse | null;
  japaneseManicure: NailType | null;
  selectedTime: string | null;
  email: string;
  onClose: () => void;
}) {
  const serviceName = japaneseManicure
    ? "Japanese Manicure"
    : `${analysis?.nail_type} + ${analysis?.design_tier}`;
  const price = japaneseManicure
    ? japaneseManicure.price
    : analysis?.estimated_price ?? 0;

  return (
    <div className="text-center py-8">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <Check className="w-8 h-8 text-green-600" />
      </div>
      <h3 className="font-semibold text-lg mb-2">You are all set!</h3>
      <p className="text-muted-foreground text-sm mb-4">
        A confirmation email will be sent to{" "}
        <span className="font-medium text-foreground">{email}</span>
      </p>
      <div className="bg-secondary rounded-xl p-4 text-left text-sm space-y-1">
        <p>
          <span className="text-muted-foreground">Service:</span>{" "}
          {serviceName}
        </p>
        <p>
          <span className="text-muted-foreground">Price:</span>{" "}
          €{price.toFixed(2)}
        </p>
        <p>
          <span className="text-muted-foreground">Date & Time:</span>{" "}
          {selectedTime && format(parseISO(selectedTime), "MMM d, yyyy 'at' h:mm a")}
        </p>
      </div>
      <button
        onClick={onClose}
        className="mt-6 bg-primary text-primary-foreground px-6 py-2.5 rounded-full text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
      >
        Done
      </button>
    </div>
  );
}

function PhotoStep({ previewUrl, selectedFile, analyzing, analyzeError, onFileSelect, onAnalyze, onJapaneseManicure }: {
  previewUrl: string | null;
  selectedFile: File | null;
  analyzing: boolean;
  analyzeError: string | null;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onAnalyze: () => void;
  onJapaneseManicure: () => void;
}) {
  return (
    <div>
      <div className="text-center">
        <div className="border-2 border-dashed border-border rounded-xl p-8 hover:border-primary/50 transition-colors">
          {previewUrl ? (
            <div className="space-y-4">
              <img
                src={previewUrl}
                alt="Nail photo preview"
                className="max-h-48 mx-auto rounded-lg object-cover"
              />
              <p className="text-sm text-muted-foreground">{selectedFile?.name}</p>
            </div>
          ) : (
            <div className="space-y-3">
              <Upload className="w-10 h-10 text-muted-foreground mx-auto" />
              <p className="text-sm text-muted-foreground">
                Upload a photo of your nails or a reference design
              </p>
              <p className="text-xs text-muted-foreground">
                JPG, PNG, GIF or WebP · Max 5 MB
              </p>
            </div>
          )}
          <label className="mt-4 inline-block cursor-pointer">
            <input
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              onChange={onFileSelect}
              className="hidden"
            />
            <span className="px-4 py-2 bg-secondary text-foreground rounded-lg text-sm font-medium hover:bg-secondary/80 transition-colors inline-block">
              {previewUrl ? "Choose Different Photo" : "Select Photo"}
            </span>
          </label>
        </div>

        {analyzeError && (
          <div className="mt-4 flex items-center gap-2 text-sm text-destructive justify-center">
            <AlertCircle className="w-4 h-4" />
            <span>{analyzeError}</span>
          </div>
        )}

        <button
          onClick={onAnalyze}
          disabled={!selectedFile || analyzing}
          className={cn(
            "mt-6 px-6 py-2.5 rounded-full text-sm font-medium transition-colors flex items-center gap-2 mx-auto cursor-pointer",
            selectedFile && !analyzing
              ? "bg-primary text-primary-foreground hover:bg-primary-dark"
              : "bg-border text-muted-foreground cursor-not-allowed"
          )}
        >
          {analyzing && <Loader2 className="w-4 h-4 animate-spin" />}
          {analyzing ? "Analyzing..." : "Get AI Estimate"}
          {!analyzing && <Sparkles className="w-4 h-4" />}
        </button>

        {/* Japanese Manicure option */}
        <div className="mt-8 pt-6 border-t border-border">
          <p className="text-xs text-muted-foreground mb-3 uppercase tracking-wide font-medium">Or choose a fixed-price service</p>
          <button
            onClick={onJapaneseManicure}
            disabled={analyzing}
            className="w-full px-5 py-4 rounded-xl border border-border bg-card hover:border-primary/50 hover:bg-primary/5 transition-colors text-left cursor-pointer group"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                <Leaf className="w-5 h-5 text-green-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm group-hover:text-primary transition-colors">Japanese Manicure</p>
                <p className="text-xs text-muted-foreground mt-0.5">€30 · 60 min</p>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0" />
            </div>
            <p className="text-xs text-muted-foreground mt-3 leading-relaxed">
              A traditional, chemical-free nail care treatment rooted in a centuries-old ritual. Focuses entirely on healing, strengthening, and adding a natural, pearly gloss to bare nails without using any gel, acrylics, or synthetic nail polish.
            </p>
          </button>
        </div>
      </div>
    </div>
  );
}

function EstimateStep({ analysis, onContinue, onBack }: {
  analysis: NailAnalysisResponse | null;
  onContinue: () => void;
  onBack: () => void;
}) {
  if (!analysis) return null;

  const confidenceColor =
    analysis.confidence === "high"
      ? "bg-green-100 text-green-700"
      : analysis.confidence === "medium"
        ? "bg-yellow-100 text-yellow-700"
        : "bg-red-100 text-red-700";

  return (
    <div>
      {/* Estimate card */}
      <div className="bg-secondary rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="font-semibold">AI Estimate</h4>
          <span className={cn("text-xs px-2 py-1 rounded-full font-medium capitalize", confidenceColor)}>
            {analysis.confidence} confidence
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-muted-foreground">Nail Type</span>
            <p className="font-medium">{analysis.nail_type}</p>
          </div>
          <div>
            <span className="text-muted-foreground">Design Tier</span>
            <p className="font-medium">{analysis.design_tier}</p>
          </div>
          <div>
            <span className="text-muted-foreground">Estimated Price</span>
            <p className="font-medium text-lg">€{analysis.estimated_price.toFixed(2)}</p>
          </div>
          <div>
            <span className="text-muted-foreground">Duration</span>
            <p className="font-medium flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {analysis.estimated_duration_minutes} min
            </p>
          </div>
        </div>

        <p className="text-sm text-muted-foreground italic">
          "{analysis.reasoning}"
        </p>
      </div>

      {/* Disclaimer */}
      <div className="mt-4 flex items-start gap-2 text-xs text-muted-foreground bg-blue-50 rounded-lg p-3">
        <Info className="w-4 h-4 mt-0.5 shrink-0 text-blue-500" />
        <span>
          This is an AI-generated estimate. The final price may vary based on the actual consultation with your nail artist.
        </span>
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-6 pt-4 border-t border-border">
        <button
          onClick={onBack}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          Back
        </button>
        <button
          onClick={onContinue}
          className="bg-primary text-primary-foreground px-5 py-2 rounded-full text-sm font-medium hover:bg-primary-dark transition-colors cursor-pointer"
        >
          Choose Date & Time
        </button>
      </div>
    </div>
  );
}

function DateTimeStep({ calendarMonth, canGoPrevMonth, datesLoading, datesError, selectedDate, timeSlots, slotsLoading, slotsError, selectedTime, onPrevMonth, onNextMonth, onSelectTime, onRetryDates, onRetrySlots, onContinue, onBack, renderCalendar }: {
  calendarMonth: Date;
  canGoPrevMonth: boolean;
  datesLoading: boolean;
  datesError: string | null;
  selectedDate: Date | null;
  timeSlots: string[];
  slotsLoading: boolean;
  slotsError: string | null;
  selectedTime: string | null;
  onPrevMonth: () => void;
  onNextMonth: () => void;
  onSelectTime: (t: string) => void;
  onRetryDates: () => void;
  onRetrySlots: () => void;
  onContinue: () => void;
  onBack: () => void;
  renderCalendar: () => React.ReactNode;
}) {
  return (
    <div>
      {/* Calendar Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={onPrevMonth}
          disabled={!canGoPrevMonth}
          className={cn(
            "p-1.5 rounded-lg transition-colors cursor-pointer",
            canGoPrevMonth ? "hover:bg-secondary text-foreground" : "text-muted-foreground/40 cursor-not-allowed"
          )}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <span className="text-sm font-medium">
          {format(calendarMonth, "MMMM yyyy")}
        </span>
        <button
          onClick={onNextMonth}
          className="p-1.5 rounded-lg hover:bg-secondary text-foreground transition-colors cursor-pointer"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Calendar */}
      {datesLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 text-primary animate-spin" />
          <span className="ml-2 text-sm text-muted-foreground">Loading dates...</span>
        </div>
      ) : datesError ? (
        <div className="text-center py-8">
          <AlertCircle className="w-6 h-6 text-destructive mx-auto mb-2" />
          <p className="text-sm text-destructive mb-3">{datesError}</p>
          <button onClick={onRetryDates} className="text-sm text-primary hover:text-primary-dark underline underline-offset-4 cursor-pointer">
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
              <span className="ml-2 text-sm text-muted-foreground">Loading times...</span>
            </div>
          )}

          {slotsError && (
            <div className="text-center py-4">
              <p className="text-sm text-destructive mb-2">{slotsError}</p>
              <button onClick={onRetrySlots} className="text-sm text-primary hover:text-primary-dark underline underline-offset-4 cursor-pointer">
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
                    onClick={() => onSelectTime(slot)}
                    className={cn(
                      "px-3 py-2 rounded-lg text-sm border transition-colors cursor-pointer",
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
        <button onClick={onBack} className="text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
          Back
        </button>
        <button
          onClick={onContinue}
          disabled={!selectedTime}
          className={cn(
            "px-5 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer",
            selectedTime
              ? "bg-primary text-primary-foreground hover:bg-primary-dark"
              : "bg-border text-muted-foreground cursor-not-allowed"
          )}
        >
          Continue
        </button>
      </div>
    </div>
  );
}

function ConfirmStep({ analysis, japaneseManicure, selectedTime, submitting, register, errors, onSubmit, onBack }: {
  analysis: NailAnalysisResponse | null;
  japaneseManicure: NailType | null;
  selectedTime: string | null;
  submitting: boolean;
  register: ReturnType<typeof useForm<ClientInfo>>["register"];
  errors: ReturnType<typeof useForm<ClientInfo>>["formState"]["errors"];
  onSubmit: (e: React.FormEvent) => void;
  onBack: () => void;
}) {
  const serviceName = japaneseManicure
    ? "Japanese Manicure"
    : `${analysis?.nail_type} + ${analysis?.design_tier}`;
  const duration = japaneseManicure
    ? japaneseManicure.duration_minutes
    : analysis?.estimated_duration_minutes ?? 0;
  const price = japaneseManicure
    ? japaneseManicure.price
    : analysis?.estimated_price ?? 0;

  return (
    <form onSubmit={onSubmit}>
      {/* Booking summary */}
      <div className="bg-secondary rounded-xl p-4 space-y-2 text-sm mb-6">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Service</span>
          <span className="font-medium">{serviceName}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Duration</span>
          <span>{duration} min</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Price</span>
          <span className="font-medium">€{price.toFixed(2)}</span>
        </div>
        <div className="border-t border-border my-2" />
        <div className="flex justify-between">
          <span className="text-muted-foreground">Date & Time</span>
          <span>
            {selectedTime && format(parseISO(selectedTime), "MMM d, yyyy 'at' h:mm a")}
          </span>
        </div>
      </div>

      {/* Client info */}
      <div className="space-y-4">
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
            <p className="text-xs text-destructive mt-1">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1.5">Phone</label>
          <input
            {...register("phone")}
            type="tel"
            placeholder="+49 123 456 7890"
            className="w-full px-3 py-2.5 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
          />
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between mt-6 pt-4 border-t border-border">
        <button
          type="button"
          onClick={onBack}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={submitting}
          className={cn(
            "px-5 py-2.5 rounded-full text-sm font-medium transition-colors flex items-center gap-2 cursor-pointer",
            submitting
              ? "bg-border text-muted-foreground cursor-not-allowed"
              : "bg-primary text-primary-foreground hover:bg-primary-dark"
          )}
        >
          {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
          {submitting ? "Booking..." : "Confirm Booking"}
        </button>
      </div>
    </form>
  );
}
