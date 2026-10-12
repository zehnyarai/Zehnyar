import 'farm_entities.dart';

abstract interface class FarmRepository {
  Future<List<Farm>> list();
  Future<Farm> get(String id);
  Future<Farm> create(FarmInput input);
  Future<Farm> update(String id, FarmInput input);
  Future<void> delete(String id);

  Future<List<Tree>> trees(String farmId);
  Future<Tree> addTree(String farmId, {required String label, int? plantedYear, String? variety});
  Future<void> removeTree(String farmId, String treeId);
}
