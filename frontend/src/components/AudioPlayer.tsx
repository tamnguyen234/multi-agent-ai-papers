import React, { useState } from 'react';
import { buildMediaUrl, formatDuration } from '../utils/mediaUrl';

interface AudioPlayerProps {
  /** Relative or absolute URL/path to audio file */
  src: string | null | undefined;
  /** Optional display title shown above the player */
  title?: string;
  /** Duration in seconds */
  durationSeconds?: number | null;
  /** Extra CSS class */
  className?: string;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ src, title, durationSeconds, className }) => {
  const [error, setError] = useState(false);
  const audioUrl = buildMediaUrl(src);

  if (!audioUrl) return null;

  if (error) {
    return (
      <div className={`audio-player-wrapper ${className ?? ''}`}>
        <p className="audio-error">⚠️ Không thể tải audio. Vui lòng thử lại sau.</p>
      </div>
    );
  }

  const duration = formatDuration(durationSeconds);

  return (
    <div className={`audio-player-wrapper ${className ?? ''}`}>
      <div className="audio-label">
        <span>🎧 {title ?? 'Audio Abstract'}</span>
        {duration && <span className="audio-duration">{duration}</span>}
      </div>
      <audio
        controls
        preload="none"
        className="audio-player"
        onError={() => setError(true)}
        key={audioUrl}
      >
        <source src={audioUrl} type="audio/mpeg" />
        <source src={audioUrl} type="audio/wav" />
        Trình duyệt không hỗ trợ audio.
      </audio>
    </div>
  );
};

export default AudioPlayer;
