import { checkMyketUpdate } from '../src/core/storeUpdates';

describe('Myket update intent', () => {
  it('requests the official intent only for Android Myket builds', async () => {
    const openURL = jest.fn().mockResolvedValue(undefined);
    expect(await checkMyketUpdate({ platform: 'android', extra: { myketBuild: true }, openURL })).toBe('requested');
    expect(openURL).toHaveBeenCalledWith('myket://check-update?id=ai.visayar.app');
  });
  it('does not run for Bazaar, direct, test or iOS builds', async () => {
    const openURL = jest.fn();
    expect(await checkMyketUpdate({ platform: 'android', extra: { bazaarIab: true }, openURL })).toBe('skipped');
    expect(await checkMyketUpdate({ platform: 'android', extra: {}, openURL })).toBe('skipped');
    expect(await checkMyketUpdate({ platform: 'ios', extra: { myketBuild: true }, openURL })).toBe('skipped');
    expect(openURL).not.toHaveBeenCalled();
  });
  it('does not fail startup when Myket is unavailable', async () => {
    const openURL = jest.fn().mockRejectedValue(new Error('not installed'));
    expect(await checkMyketUpdate({ platform: 'android', extra: { myketBuild: true }, openURL })).toBe('unavailable');
  });
});
