import { useState, type ReactNode } from 'react';
import type { DragEndEvent } from '@dnd-kit/core';
import { DndContext, PointerSensor, closestCenter, useSensor, useSensors } from '@dnd-kit/core';
import { SortableContext, arrayMove, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

import { useActivityAlternatives } from '../hooks/useActivityAlternatives';
import { useRegenerateDay } from '../hooks/useRegenerateDay';
import { useWalkingRoute } from '../hooks/useWalkingRoute';
import type { Activity, DayItinerary, ScheduledActivity } from '../services/types';

interface SortableStopProps {
  item: ScheduledActivity;
  selected: boolean;
  swapping: boolean;
  onSelect: () => void;
  onRemove: () => void;
  onSwapToggle: () => void;
  children?: ReactNode;
}

function SortableStop({ item, selected, swapping, onSelect, onRemove, onSwapToggle, children }: SortableStopProps) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: item.activity.id });
  const style = { transform: CSS.Transform.toString(transform), transition };

  return (
    <li
      ref={setNodeRef}
      style={style}
      className={selected ? 'itinerary-stop itinerary-stop--selected' : 'itinerary-stop'}
      onClick={onSelect}
    >
      <span className='itinerary-stop__drag-handle' aria-label='Drag to reorder' {...attributes} {...listeners}>
        ⠿
      </span>{' '}
      <strong>
        {item.start_time}–{item.end_time}
      </strong>{' '}
      {item.activity.name} (${item.activity.price})
      <button
        type='button'
        className='button button--tiny'
        onClick={(event) => {
          event.stopPropagation();
          onSwapToggle();
        }}
      >
        {swapping ? 'Cancel' : 'Swap'}
      </button>
      <button
        type='button'
        className='button button--tiny'
        onClick={(event) => {
          event.stopPropagation();
          onRemove();
        }}
      >
        Remove
      </button>
      {children}
    </li>
  );
}

interface ItineraryDayEditorProps {
  destinationId: number;
  day: DayItinerary;
  otherDaysActivityIds: number[];
  budget?: number;
  interests?: string;
  totalDays: number;
  selectedActivityId: number | null;
  onSelectActivity: (id: number) => void;
  onChange: (updatedDay: DayItinerary) => void;
}

export default function ItineraryDayEditor({
  destinationId,
  day,
  otherDaysActivityIds,
  budget,
  interests,
  totalDays,
  selectedActivityId,
  onSelectActivity,
  onChange,
}: ItineraryDayEditorProps) {
  const [swappingActivityId, setSwappingActivityId] = useState<number | null>(null);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));
  const alternativesMutation = useActivityAlternatives();
  const regenerateMutation = useRegenerateDay(destinationId);

  const routePoints = day.activities.map((item) => ({ lat: item.activity.latitude, lon: item.activity.longitude }));
  const walkingRoute = useWalkingRoute(routePoints);
  const flatTravelMinutes = day.activities.reduce((sum, item) => sum + item.activity.travel_minutes, 0);
  const displayTravelMinutes = walkingRoute.data ? walkingRoute.data.durationMinutes : flatTravelMinutes;
  const displayCost = day.activities.reduce((sum, item) => sum + item.activity.price, 0);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = day.activities.findIndex((item) => item.activity.id === active.id);
    const newIndex = day.activities.findIndex((item) => item.activity.id === over.id);
    if (oldIndex === -1 || newIndex === -1) return;
    onChange({ ...day, activities: arrayMove(day.activities, oldIndex, newIndex) });
  };

  const handleRemove = (activityId: number) => {
    onChange({ ...day, activities: day.activities.filter((item) => item.activity.id !== activityId) });
  };

  const handleSwapToggle = (activityId: number) => {
    if (swappingActivityId === activityId) {
      setSwappingActivityId(null);
      return;
    }
    setSwappingActivityId(activityId);
    const excludeIds = [...otherDaysActivityIds, ...day.activities.map((item) => item.activity.id)];
    alternativesMutation.mutate({ activityId, excludeIds });
  };

  const handleSwapPick = (activityId: number, replacement: Activity) => {
    onChange({
      ...day,
      activities: day.activities.map((item) =>
        item.activity.id === activityId ? { ...item, activity: replacement } : item,
      ),
    });
    setSwappingActivityId(null);
  };

  const handleRegenerateDay = () => {
    regenerateMutation.mutate(
      { day: day.day, days: totalDays, lockedActivityIds: otherDaysActivityIds, budget, interests },
      { onSuccess: (updatedDay) => onChange(updatedDay) },
    );
  };

  return (
    <article className='result-card'>
      <div className='itinerary-day-header'>
        <h4>Day {day.day}</h4>
        <button
          type='button'
          className='button button--secondary button--tiny'
          onClick={handleRegenerateDay}
          disabled={regenerateMutation.isPending}
        >
          {regenerateMutation.isPending ? 'Regenerating…' : 'Regenerate day'}
        </button>
      </div>

      {regenerateMutation.isError && <p className='itinerary-warning'>Could not regenerate this day.</p>}

      {day.activities.length === 0 ? (
        <p>No activities scheduled.</p>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext
            items={day.activities.map((item) => item.activity.id)}
            strategy={verticalListSortingStrategy}
          >
            <ul>
              {day.activities.map((item) => (
                <SortableStop
                  key={item.activity.id}
                  item={item}
                  selected={item.activity.id === selectedActivityId}
                  swapping={swappingActivityId === item.activity.id}
                  onSelect={() => onSelectActivity(item.activity.id)}
                  onRemove={() => handleRemove(item.activity.id)}
                  onSwapToggle={() => handleSwapToggle(item.activity.id)}
                >
                  {swappingActivityId === item.activity.id && (
                    <div className='itinerary-alternatives'>
                      {alternativesMutation.isPending && <p>Finding alternatives…</p>}
                      {alternativesMutation.isError && <p>Could not load alternatives.</p>}
                      {alternativesMutation.data && alternativesMutation.data.length === 0 && (
                        <p>No alternatives found for this destination.</p>
                      )}
                      {alternativesMutation.data?.map((alternative) => (
                        <button
                          key={alternative.id}
                          type='button'
                          className='chip'
                          onClick={() => handleSwapPick(item.activity.id, alternative)}
                        >
                          {alternative.name}
                        </button>
                      ))}
                    </div>
                  )}
                </SortableStop>
              ))}
            </ul>
          </SortableContext>
        </DndContext>
      )}

      <p>
        <strong>Day total:</strong> ${displayCost} · {displayTravelMinutes} min travel
        {walkingRoute.isError && ' (estimated)'}
      </p>
    </article>
  );
}
